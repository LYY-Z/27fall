"""
XArmcontroller_v2.py

单类双臂机械臂控制器，每条臂对应一路 CAN 总线，含 7 个本体电机 + 1 个夹爪电机。

公开 API（XArmController）：
    arm_control          — 7轴插值位置控制（minimum-jerk 或 linear）
    arm_torque_control   — 7轴力矩控制
    gripper_control      — 夹爪插值位置控制
    get_arm_states       — 读取 7 轴状态
    get_gripper_state    — 读取夹爪状态
    refresh_arm          — 零力矩触发 7 轴反馈（使能未控制时刷新状态）
    recv_arm             — 接收 7 轴反馈帧
    refresh_gripper      — 零力矩触发夹爪反馈
    recv_gripper         — 接收夹爪反馈帧
    enable / disable     — 使能 / 失能全部电机

side 参数：
    "left"  — 仅操作左臂
    "right" — 仅操作右臂
    None    — 操作所有已配置的臂（默认）
"""

import can
import math
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union


# ── 关节机械限位 [min_rad, max_rad]（J1-J7 + GRIPPER）──────────────────────
MECH_LIM: List[List[float]] = [
    [math.radians(-80),  math.radians(200)],   # J1
    [math.radians(-100), math.radians(100)],   # J2
    [math.radians(-90),  math.radians(90)],    # J3
    [math.radians(0),    math.radians(140)],   # J4
    [math.radians(-90),  math.radians(90)],    # J5
    [math.radians(-45),  math.radians(45)],    # J6
    [math.radians(-90),  math.radians(90)],    # J7
    [math.radians(-60),  math.radians(0)],     # GRIPPER
]

def _check_joint_limits(positions: List[float], joint_offset: int = 0):
    """检查关节角是否超出机械限位，超出则打印错误信息并退出程序。"""
    for i, pos in enumerate(positions):
        idx = joint_offset + i
        lo, hi = MECH_LIM[idx]
        if pos < lo or pos > hi:
            joint_name = f"J{idx + 1}" if idx < 7 else "GRIPPER"
            print(
                f"[XArmController] 错误：{joint_name} 目标角 {math.degrees(pos):.2f}° "
                f"超出机械限位 [{math.degrees(lo):.1f}°, {math.degrees(hi):.1f}°]，程序退出。"
            )
            sys.exit(1)

# ── 电机限制 [位置 rad, 速度 rad/s, 扭矩 Nm] ────────────────────────────────
LIMIT_DM4310 = [12.5, 30,  10]
LIMIT_DM4340 = [12.5,  8,  28]
LIMIT_DM8006 = [12.5, 45,  40]
LIMIT_DM8009 = [12.5, 45,  54]
LIMIT_DM6006 = [12.5, 45,  12]

ARM_7DOF_LIMITS: List[List[float]] = [
    LIMIT_DM8009,   # J1
    LIMIT_DM8009,   # J2
    LIMIT_DM4340,   # J3
    LIMIT_DM4340,   # J4
    LIMIT_DM4310,   # J5
    LIMIT_DM4310,   # J6
    LIMIT_DM4310,   # J7
]
LIMIT_GRIPPER = LIMIT_DM4310

# ── 默认 PD 增益 ─────────────────────────────────────────────────────────────
#   7 个本体关节
ARM_KP_DEFAULT: List[float] = [280.0, 280.0, 240.0, 240.0, 35.0, 35.0, 35.0]
ARM_KD_DEFAULT: List[float] = [  5.0,   5.0,   5.0,   5.0,  1.2,  1.2,  1.2]
# 注：DM 电机 MIT 协议 kd 编码范围为 [0, 5]，原始值 20/10 超出上限，钳位至 5.0
#   夹爪
GRIPPER_KP_DEFAULT: float = 10.0
GRIPPER_KD_DEFAULT: float =  0.2

# 8 轴 ID：本体 0x01-0x07，夹爪 0x08；反馈 ID = slave + 0x10
_SLAVE_IDS  = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]
_MASTER_IDS = [s + 0x10 for s in _SLAVE_IDS]


# ── 数据结构 ─────────────────────────────────────────────────────────────────
@dataclass
class MotorState:
    can_id:      int
    master_id:   int
    limit:       List[float]
    position:    float = 0.0
    velocity:    float = 0.0
    torque:      float = 0.0
    last_update: float = field(default_factory=time.monotonic)


@dataclass
class MITParam:
    kp:  float = 0.0
    kd:  float = 0.0
    q:   float = 0.0
    dq:  float = 0.0
    tau: float = 0.0


# ── 轨迹函数 ─────────────────────────────────────────────────────────────────
def _min_jerk(t: float) -> float:
    """最小加加速度曲线：s = 10t³ - 15t⁴ + 6t⁵，t ∈ [0,1]"""
    return 10 * t**3 - 15 * t**4 + 6 * t**5

_PROFILES = {"minjerk": _min_jerk, "linear": lambda t: t}


# ── 单条 CAN 总线（内部，管理 8 个电机）────────────────────────────────────
class _ArmBus:
    _ARM_N   = 7   # 本体电机数量
    _GRIP_IDX = 7  # 夹爪在 _motors 中的索引

    def __init__(self, channel: str,
                 arm_limits: List[List[float]] = ARM_7DOF_LIMITS,
                 gripper_limit: List[float]    = LIMIT_GRIPPER):
        self.channel = channel
        all_limits = arm_limits + [gripper_limit]
        assert len(all_limits) == 8

        self._motors: List[MotorState] = []
        self._id_map: Dict[int, MotorState] = {}

        for limit, sid, mid in zip(all_limits, _SLAVE_IDS, _MASTER_IDS):
            m = MotorState(can_id=sid, master_id=mid, limit=limit)
            self._motors.append(m)
            self._id_map[sid] = m
            self._id_map[mid] = m

        # 分组 master ID，便于分别接收
        self._arm_master_ids:  Set[int] = {m.master_id for m in self._motors[:7]}
        self._grip_master_ids: Set[int] = {self._motors[7].master_id}

        self._bus = can.Bus(channel=channel, interface="socketcan", fd=True)

    # ── 编解码 ───────────────────────────────────────────────────────────────
    @staticmethod
    def _f2u(x: float, xmin: float, xmax: float, bits: int) -> int:
        return int((x - xmin) / (xmax - xmin) * ((1 << bits) - 1))

    @staticmethod
    def _u2f(x: int, xmin: float, xmax: float, bits: int) -> float:
        return x / ((1 << bits) - 1) * (xmax - xmin) + xmin

    # MIT 协议硬件编码范围
    _KP_MAX  = 500.0
    _KD_MAX  =   5.0

    def _pack(self, m: MotorState, p: MITParam) -> bytes:
        pm, vm, tm = m.limit
        # 钳位到硬件允许范围，防止超范围值导致字节溢出
        q   = max(-pm,  min(pm,  p.q))
        dq  = max(-vm,  min(vm,  p.dq))
        kp  = max(0.0,  min(self._KP_MAX, p.kp))
        kd  = max(0.0,  min(self._KD_MAX, p.kd))
        tau = max(-tm,  min(tm,  p.tau))
        q_u   = self._f2u(q,   -pm, pm, 16)
        dq_u  = self._f2u(dq,  -vm, vm, 12)
        kp_u  = self._f2u(kp,  0, self._KP_MAX, 12)
        kd_u  = self._f2u(kd,  0, self._KD_MAX, 12)
        tau_u = self._f2u(tau, -tm, tm, 12)
        d = bytearray(8)
        d[0] = (q_u >> 8) & 0xFF
        d[1] = q_u & 0xFF
        d[2] = dq_u >> 4
        d[3] = ((dq_u & 0xF) << 4) | ((kp_u >> 8) & 0xF)
        d[4] = kp_u & 0xFF
        d[5] = kd_u >> 4
        d[6] = ((kd_u & 0xF) << 4) | ((tau_u >> 8) & 0xF)
        d[7] = tau_u & 0xFF
        return bytes(d)

    def _parse(self, msg: can.Message):
        d = msg.data
        if len(d) < 6:
            return
        m = self._id_map.get(msg.arbitration_id)
        if m is None:
            return
        pm, vm, tm = m.limit
        m.position    = self._u2f((d[1] << 8) | d[2],           -pm, pm, 16)
        m.velocity    = self._u2f((d[3] << 4) | (d[4] >> 4),    -vm, vm, 12)
        m.torque      = self._u2f(((d[4] & 0xF) << 8) | d[5],   -tm, tm, 12)
        m.last_update = time.monotonic()

    # ── 发送 ─────────────────────────────────────────────────────────────────
    def _send(self, arb_id: int, data: bytes):
        self._bus.send(can.Message(
            arbitration_id=arb_id, data=data,
            is_fd=True, is_extended_id=False))

    def _send_cmd(self, slave_id: int, cmd: int):
        self._send(slave_id, bytes([0xFF] * 7 + [cmd]))

    def _send_mit(self, m: MotorState, p: MITParam):
        self._send(m.can_id, self._pack(m, p))

    # ── 接收（可按组过滤）────────────────────────────────────────────────────
    def _recv(self, target_ids: Set[int], timeout: float):
        received: Set[int] = set()
        deadline = time.perf_counter() + timeout
        while received != target_ids:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break
            msg = self._bus.recv(timeout=remaining)
            if msg is None:
                break
            # ✓ 关键修复：无论是否是目标消息，都应该解析并更新状态
            # 这避免了"垃圾消息"在缓冲区中积累，确保 arm_control 之后
            # gripper_control 的通信时序一致
            self._parse(msg)
            if msg.arbitration_id in target_ids:
                received.add(msg.arbitration_id)

    def recv_arm(self, timeout: float = 0.01):
        """接收 7 个本体电机的反馈帧。"""
        self._recv(self._arm_master_ids, timeout)

    def recv_gripper(self, timeout: float = 0.01):
        """接收夹爪电机的反馈帧。"""
        self._recv(self._grip_master_ids, timeout)

    # ── 刷新（触发反馈）─────────────────────────────────────────────────────
    def refresh_arm(self, timeout: float = 0.02, active: bool = True):
        """向 7 个本体电机发送 MIT 帧触发状态回报，刷新缓存。

        Args:
            timeout: 等待反馈超时 (s)
            active:  True（默认）→ 以默认增益保持当前位置，触发反馈的同时
                         维持力矩，适合运动中间读取状态，不会掉臂。
                     False → 发零力矩帧，适合使能后、开始控制前的初始读取。
        """
        if active:
            for m, kpi, kdi in zip(self._motors[:7],
                                   ARM_KP_DEFAULT, ARM_KD_DEFAULT):
                self._send_mit(m, MITParam(kp=kpi, kd=kdi,
                                           q=m.position, dq=0.0, tau=0.0))
        else:
            for m in self._motors[:7]:
                self._send_mit(m, MITParam(q=m.position))
        self.recv_arm(timeout)

    def refresh_gripper(self, timeout: float = 0.02, active: bool = False):
        """向夹爪电机发送 MIT 帧触发状态回报，刷新缓存。

        Args:
            active: True → 保持当前位置同时读取；False（默认）→ 零力矩读取。
        """
        m = self._motors[7]
        if active:
            self._send_mit(m, MITParam(kp=GRIPPER_KP_DEFAULT, kd=GRIPPER_KD_DEFAULT,
                                       q=m.position, dq=0.0, tau=0.0))
        else:
            self._send_mit(m, MITParam(q=m.position))
        self.recv_gripper(timeout)

    # ── 使能 / 失能 ───────────────────────────────────────────────────────────
    def _toggle(self, motor_idx: int, cmd: int, repeat: int):
        sid = self._motors[motor_idx].can_id
        for _ in range(repeat):
            self._send_cmd(sid, cmd)
            time.sleep(0.002)

    def enable(self, repeat: int = 3):
        for m in self._motors:
            for _ in range(repeat):
                self._send_cmd(m.can_id, 0xFC)
                time.sleep(0.002)
        time.sleep(0.2)

    def disable(self, repeat: int = 3):
        for m in self._motors:
            for _ in range(repeat):
                self._send_cmd(m.can_id, 0xFD)
                time.sleep(0.002)

    def set_zero(self, motor_idx: int):
        self._send_cmd(self._motors[motor_idx].can_id, 0xFE)
        time.sleep(0.002)

    def mit_control_one(self, motor_idx: int, p: MITParam):
        """对指定电机发送 MIT 控制指令（按索引）。"""
        m = self._motors[motor_idx]
        self._send_mit(m, p)

    def mit_control_all(self, params: List[MITParam]):
        """对该总线全部电机发送 MIT 控制指令。"""
        assert len(params) == len(self._motors)-1, \
            f"params 数量({len(params)}) 与电机数量({len(self._motors)-1})不符"
        for m, p in zip(self._motors[:-1], params):
            self._send_mit(m, p)
    # ── 本体 7 轴控制 ─────────────────────────────────────────────────────────
    def arm_control(
        self,
        positions: List[float],
        kp: Union[float, List[float]] = None,
        kd: Union[float, List[float]] = None,
        duration: float               = 1.0,
        hz: int                       = 200,
        tau_ff: Optional[List[float]] = None,
        profile: str                  = "minjerk",
    ):
        """7 轴插值位置控制（minimum-jerk 轨迹）。运动前自动刷新起始位置。

        Args:
            positions: 目标关节角 (rad), 长度 7
            kp:        位置增益，标量或长度 7 的列表（默认 ARM_KP_DEFAULT）
            kd:        阻尼增益，标量或长度 7 的列表（默认 ARM_KD_DEFAULT）
            duration:  运动时长 (s)
            hz:        控制频率 (Hz)
            tau_ff:    前馈力矩列表（可选）
            profile:   "minjerk"（默认）或 "linear"
        """
        assert len(positions) == 7, "positions 长度须为 7"
        assert profile in _PROFILES, f"profile 须为 {list(_PROFILES)}"
        _check_joint_limits(positions, joint_offset=0)

        kp_list = (ARM_KP_DEFAULT if kp is None
                   else ([kp] * 7 if isinstance(kp, (int, float)) else list(kp)))
        kd_list = (ARM_KD_DEFAULT if kd is None
                   else ([kd] * 7 if isinstance(kd, (int, float)) else list(kd)))
        assert len(kp_list) == 7, "kp 列表长度须为 7"
        assert len(kd_list) == 7, "kd 列表长度须为 7"

        tff    = tau_ff if tau_ff is not None else [0.0] * 7
        s_func = _PROFILES[profile]
        
        # ── 先用缓存位置顶住臂，再刷新真实起点（防止 recv 期间掉臂）────────
        for m, kpi, kdi in zip(self._motors[:7], kp_list, kd_list):
            self._send_mit(m, MITParam(kp=kpi, kd=kdi,
                                       q=m.position, dq=0.0, tau=0.0))
        self.recv_arm(timeout=0.05)
        starts = [m.position for m in self._motors[:7]]

        dt    = 1.0 / hz
        steps = max(1, int(duration * hz))
        # ── 接入稳定阶段（约 25ms，全量增益）────────────────────────────────
        settle_n = max(1, int(0.025 * hz))
        t0 = time.perf_counter()
        for i in range(settle_n):
            for m, sp, tf, kpi, kdi in zip(
                    self._motors[:7], starts, tff, kp_list, kd_list):
                self._send_mit(m, MITParam(kp=kpi, kd=kdi, q=sp, dq=0.0, tau=tf))
            self.recv_arm(timeout=dt * 0.5)
            wait = t0 + (i + 1) * dt - time.perf_counter()
            if wait > 0:
                time.sleep(wait)

        # ── 插值轨迹 ────────────────────────────────────────────────────────
        t0 = time.perf_counter()
        for step in range(steps + 1):
            s = s_func(step / steps)
            for m, sp, tp, tf, kpi, kdi in zip(
                    self._motors[:7], starts, positions, tff, kp_list, kd_list):
                self._send_mit(m, MITParam(
                    kp=kpi, kd=kdi,
                    q=sp + s * (tp - sp),
                    dq=0.0, tau=tf))
            self.recv_arm(timeout=dt * 0.5)
            wait = t0 + (step + 1) * dt - time.perf_counter()
            if wait > 0:
                time.sleep(wait)

        # ── 插值结束后保持目标位置（防止下次调用前掉臂）────────────────────
        for m, tp, tf, kpi, kdi in zip(
                self._motors[:7], positions, tff, kp_list, kd_list):
            self._send_mit(m, MITParam(kp=kpi, kd=kdi,
                                       q=tp, dq=0.0, tau=tf))
        # 必须接收反馈，否则 CAN 缓冲区会积累 arm 消息，影响后续 gripper 通信时序
        self.recv_arm(timeout=0.05)

    
    def arm_torque_control(self, taus: List[float], kd: float = 0.0):
        """7 轴力矩控制（纯力矩前馈，kp=0）。"""
        assert len(taus) == 7, "taus 长度须为 7"
        for m, tau in zip(self._motors[:7], taus):
            self._send_mit(m, MITParam(kd=kd, tau=tau))

    # ── 夹爪控制 ──────────────────────────────────────────────────────────────
    def gripper_control(
        self,
        pos: float,
        kp: float      = GRIPPER_KP_DEFAULT,
        kd: float      = GRIPPER_KD_DEFAULT,
        duration: float = 0.8,
        hz: int        = 100,
        profile: str   = "minjerk",
    ):
        """夹爪插值位置控制。

        Args:
            pos:      目标位置 (rad)
            kp, kd:   PD 增益
            duration: 运动时长 (s)
            hz:       控制频率 (Hz)
            profile:  "minjerk" 或 "linear"
        """
        assert profile in _PROFILES
        _check_joint_limits([pos], joint_offset=7)
        m      = self._motors[7]
        s_func = _PROFILES[profile]

        self.recv_gripper(timeout=0.05)
        start = m.position

        dt    = 1.0 / hz
        steps = max(1, int(duration * hz))
        t0    = time.perf_counter()

        for step in range(steps + 1):
            s = s_func(step / steps)
            self._send_mit(m, MITParam(kp=kp, kd=kd, q=start + s * (pos - start)))
            self.recv_gripper(timeout=dt * 0.5)
            wait = t0 + (step + 1) * dt - time.perf_counter()
            if wait > 0:
                time.sleep(wait)

    # ── 状态读取 ──────────────────────────────────────────────────────────────
    def get_arm_states(self) -> List[MotorState]:
        return list(self._motors[:7])

    def get_gripper_state(self) -> MotorState:
        return self._motors[7]

    def close(self):
        self._bus.shutdown()


# ── 公开控制器 ───────────────────────────────────────────────────────────────
class XArmController:
    """双臂机械臂控制器。

    Args:
        left_channel:  左臂 CAN 通道名（如 "can0"），不使用左臂时传 None
        right_channel: 右臂 CAN 通道名（如 "can1"），不使用右臂时传 None
        arm_limits:    7 轴电机限制（默认 ARM_7DOF_LIMITS）
        gripper_limit: 夹爪电机限制（默认 LIMIT_GRIPPER）

    典型用法::

        # 仅左臂
        ctrl = XArmController(left_channel="can0")

        # 仅右臂
        ctrl = XArmController(right_channel="can1")

        # 双臂
        ctrl = XArmController(left_channel="can0", right_channel="can1")

    所有控制函数均接受 side 参数：
        side=None    → 所有已配置的臂（默认）
        side="left"  → 仅左臂
        side="right" → 仅右臂
    """

    def __init__(
        self,
        left_channel:   Optional[str]        = None,
        right_channel:  Optional[str]        = None,
        arm_limits:     List[List[float]]    = ARM_7DOF_LIMITS,
        gripper_limit:  List[float]          = LIMIT_GRIPPER,
    ):
        self._buses: Dict[str, _ArmBus] = {}
        if left_channel:
            self._buses["left"]  = _ArmBus(left_channel,  arm_limits, gripper_limit)
        if right_channel:
            self._buses["right"] = _ArmBus(right_channel, arm_limits, gripper_limit)
        assert self._buses, "至少需要传入 left_channel 或 right_channel 之一"
        print(f"[XArmController] 已初始化: {list(self._buses)}")

    # ── 内部工具 ──────────────────────────────────────────────────────────────
    def _targets(self, side: Optional[str]) -> List[_ArmBus]:
        if side is None:
            return list(self._buses.values())
        b = self._buses.get(side)
        if b is None:
            raise KeyError(f"'{side}' 未配置，可用: {list(self._buses)}")
        return [b]

    def _run_parallel(self, fn_args: List[tuple]):
        """并发执行多个 (func, args, kwargs) 任务（用于双臂同时运动）。"""
        if len(fn_args) == 1:
            fn, args, kwargs = fn_args[0]
            fn(*args, **kwargs)
            return
        threads = [
            threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
            for fn, args, kwargs in fn_args
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    # ── 使能 / 失能 ───────────────────────────────────────────────────────────
    def enable(self, side: Optional[str] = None):
        """使能电机（本体 + 夹爪）。"""
        for bus in self._targets(side):
            print(f"  使能 {bus.channel} ...")
            bus.enable()
        print("[XArmController] 使能完成")

    def disable(self, side: Optional[str] = None):
        """失能电机（本体 + 夹爪）。"""
        for bus in self._targets(side):
            print(f"  失能 {bus.channel} ...")
            bus.disable()

    def set_zero(self, motor_idx: int, side: Optional[str] = None):
        """设置指定电机的零点。"""
        for bus in self._targets(side):
            bus.set_zero(motor_idx)

    # ── 7 轴本体控制 ──────────────────────────────────────────────────────────
    def arm_control(
        self,
        positions: Union[List[float], Dict[str, List[float]]],
        kp: Union[float, List[float], None]                          = None,
        kd: Union[float, List[float], None]                          = None,
        duration: float                                              = 2.0,
        hz: int                                                      = 200,
        tau_ff: Optional[Union[List[float], Dict[str, List[float]]]] = None,
        profile: str                                                 = "minjerk",
        side: Optional[str]                                          = None,
    ):
        """7 轴插值位置控制（minimum-jerk 轨迹）。

        Args:
            positions: 单臂时为 List[float](长度7)；
                       双臂且目标不同时为 {"left": [...], "right": [...]}
            kp:        位置增益，标量或长度 7 的列表（默认 ARM_KP_DEFAULT）
            kd:        阻尼增益，标量或长度 7 的列表（默认 ARM_KD_DEFAULT）
            duration:  运动时长 (s)，默认 1.0
            hz:        控制频率 (Hz)，默认 200
            tau_ff:    前馈力矩，格式与 positions 相同（可选）
            profile:   "minjerk"（默认）或 "linear"
            side:      "left" / "right" / None（全部）
        """
        buses = self._targets(side)
        tasks = []
        for bus in buses:
            name = [k for k, v in self._buses.items() if v is bus][0]
            pos = positions[name] if isinstance(positions, dict) else positions
            tff = (tau_ff[name] if isinstance(tau_ff, dict) else tau_ff) if tau_ff else None
            tasks.append((bus.arm_control, (pos,),
                          dict(kp=kp, kd=kd, duration=duration,
                               hz=hz, tau_ff=tff, profile=profile)))
        self._run_parallel(tasks)

    def arm_hold(
        self,
        positions: Optional[Union[List[float], Dict[str, List[float]]]] = None,
        kp: Union[float, List[float], None]                             = None,
        kd: Union[float, List[float], None]                             = None,
        tau_ff: Optional[Union[List[float], Dict[str, List[float]]]]    = None,
        duration: float                                                 = float("inf"),
        hz: int                                                         = 200,
        side: Optional[str]                                             = None,
    ):
        """以高 Kp 持续固定机械臂（阻塞）。

        Args:
            positions: 保持目标角，None 表示保持当前缓存位置；
                       双臂不同目标传 {"left": [...], "right": [...]}
            kp, kd:    增益（默认 ARM_KP_DEFAULT / ARM_KD_DEFAULT）
            tau_ff:    前馈力矩（可选）
            duration:  保持时长 (s)，默认 inf（永久，Ctrl-C 退出）
            hz:        发帧频率 (Hz)
            side:      "left" / "right" / None（全部）
        """
        buses = self._targets(side)
        tasks = []
        for bus in buses:
            name = [k for k, v in self._buses.items() if v is bus][0]
            pos = (positions[name] if isinstance(positions, dict) else positions) \
                  if positions is not None else None
            tff = (tau_ff[name] if isinstance(tau_ff, dict) else tau_ff) \
                  if tau_ff is not None else None
            tasks.append((bus.arm_hold, (),
                          dict(positions=pos, kp=kp, kd=kd, tau_ff=tff,
                               duration=duration, hz=hz)))
        self._run_parallel(tasks)

    def arm_torque_control(
        self,
        taus: Union[List[float], Dict[str, List[float]]],
        kd: float              = 0.0,
        side: Optional[str]    = None,
    ):
        """7 轴力矩控制（kp=0）。

        Args:
            taus: List[float](长度7) 或 {"left": [...], "right": [...]}
            kd:   阻尼增益（可选）
        """
        for bus in self._targets(side):
            name = [k for k, v in self._buses.items() if v is bus][0]
            t = taus[name] if isinstance(taus, dict) else taus
            bus.arm_torque_control(t, kd)

    # ── 单电机控制 ────────────────────────────────────────────────────────────
    def mit_control_one(
        self,
        motor_idx: int,
        p: MITParam,
        side: Optional[str] = None,
    ):
        """对指定臂的指定电机发送 MIT 指令。

        Args:
            motor_idx: 电机索引（0-7，其中 0-6 为本体，7 为夹爪）
            p:         MIT 参数对象
            side:      "left" / "right" / None（全部）
        """
        for bus in self._targets(side):
            bus.mit_control_one(motor_idx, p)

    # ── 单总线全部电机控制 ────────────────────────────────────────────────────
    def mit_control_all(
        self,
        params: Union[List[MITParam], Dict[str, List[MITParam]]],
        side: Optional[str] = None,
    ):
        """对指定臂的全部电机发送 MIT 指令。

        Args:
            params: List[MITParam](长度8) 或 {"left": [...], "right": [...]}
            side:   "left" / "right" / None（全部）
        """
        for bus in self._targets(side):
            name = [k for k, v in self._buses.items() if v is bus][0]
            p = params[name] if isinstance(params, dict) else params
            bus.mit_control_all(p)

    # ── 夹爪控制 ──────────────────────────────────────────────────────────────
    def gripper_control(
        self,
        pos: Union[float, Dict[str, float]],
        kp: float              = GRIPPER_KP_DEFAULT,
        kd: float              = GRIPPER_KD_DEFAULT,
        duration: float        = 0.8,
        hz: int                = 100,
        profile: str           = "minjerk",
        side: Optional[str]    = None,
    ):
        """夹爪插值位置控制。

        Args:
            pos:      目标位置 (rad) 或 {"left": float, "right": float}
            kp, kd:   PD 增益
            duration: 运动时长 (s)
            hz:       控制频率 (Hz)
            profile:  "minjerk" 或 "linear"
        """
        buses = self._targets(side)
        tasks = []
        for bus in buses:
            name = [k for k, v in self._buses.items() if v is bus][0]
            p = pos[name] if isinstance(pos, dict) else pos
            tasks.append((bus.gripper_control, (p, kp, kd),
                          dict(duration=duration, hz=hz, profile=profile)))
        self._run_parallel(tasks)

    # ── 接收 / 刷新 ───────────────────────────────────────────────────────────
    def recv_arm(self, side: Optional[str] = None, timeout: float = 0.01):
        """接收 7 个本体电机的反馈帧，更新缓存状态。"""
        for bus in self._targets(side):
            bus.recv_arm(timeout)

    def recv_gripper(self, side: Optional[str] = None, timeout: float = 0.01):
        """接收夹爪电机的反馈帧，更新缓存状态。"""
        for bus in self._targets(side):
            bus.recv_gripper(timeout)

    def refresh_arm(self, side: Optional[str] = None,
                    timeout: float = 0.02, active: bool = True):
        """触发 7 轴反馈并刷新状态。

        Args:
            active: True（默认）→ 保持当前位置同时读取，运动中间调用不掉臂。
                    False → 零力矩读取，适合使能后控制前的初始状态读取。
        """
        for bus in self._targets(side):
            bus.refresh_arm(timeout, active=active)

    def refresh_gripper(self, side: Optional[str] = None,
                        timeout: float = 0.02, active: bool = False):
        """触发夹爪反馈并刷新状态。

        Args:
            active: True → 保持当前位置同时读取；False（默认）→ 零力矩读取。
        """
        for bus in self._targets(side):
            bus.refresh_gripper(timeout, active=active)

    # ── 状态读取 ──────────────────────────────────────────────────────────────
    def get_arm_states(
        self, side: Optional[str] = None
    ) -> Union[List[MotorState], Dict[str, List[MotorState]]]:
        """返回 7 个本体电机状态。
        单臂配置或指定 side 时返回 List[MotorState]；
        双臂且 side=None 时返回 {"left": [...], "right": [...]}.
        """
        buses = self._targets(side)
        if len(buses) == 1:
            return buses[0].get_arm_states()
        return {k: v.get_arm_states() for k, v in self._buses.items()}

    def get_gripper_state(
        self, side: Optional[str] = None
    ) -> Union[MotorState, Dict[str, MotorState]]:
        """返回夹爪电机状态。
        单臂或指定 side 时返回 MotorState；双臂且 side=None 时返回 dict。
        """
        buses = self._targets(side)
        if len(buses) == 1:
            return buses[0].get_gripper_state()
        return {k: v.get_gripper_state() for k, v in self._buses.items()}

    def close(self):
        for bus in self._buses.values():
            bus.close()
        print("[XArmController] 已关闭所有 CAN 总线")


if __name__ == "__main__":
    TARGET = [0.149, 0.53, -0.3313, 1.272, 0.521, 0.05855, 0.605]
    ctrl = XArmController(right_channel="can0")
    ctrl.enable()

    ctrl.arm_control(positions=TARGET)
    ctrl.refresh_arm()
    states = ctrl.get_arm_states()
    print("关节角:", [f"{s.position:.3f}" for s in states])
    print("关节速度:", [f"{s.velocity:.3f}" for s in states])
    print("关节力矩:", [f"{s.torque:.3f}" for s in states])

    ctrl.arm_control(positions=[0.0]*7)
    ctrl.refresh_arm()
    states = ctrl.get_arm_states()
    print("关节角:", [f"{s.position:.3f}" for s in states])
    print("关节速度:", [f"{s.velocity:.3f}" for s in states])
    print("关节力矩:", [f"{s.torque:.3f}" for s in states])
    
    
    ctrl.arm_control(positions=TARGET)
    ctrl.refresh_arm()
    states = ctrl.get_arm_states()
    print("关节角:", [f"{s.position:.3f}" for s in states])
    print("关节速度:", [f"{s.velocity:.3f}" for s in states])
    print("关节力矩:", [f"{s.torque:.3f}" for s in states])

    ctrl.arm_control(positions=[0.0]*7)
    ctrl.refresh_arm()
    states = ctrl.get_arm_states()
    print("关节角:", [f"{s.position:.3f}" for s in states])
    print("关节速度:", [f"{s.velocity:.3f}" for s in states])
    print("关节力矩:", [f"{s.torque:.3f}" for s in states])

    # try:
    #     ctrl.enable()
    #     ctrl.refresh_arm()
    #     ctrl.refresh_gripper()

    #     states = ctrl.get_arm_states()
    #     print("初始关节角:", [f"{s.position:.3f}" for s in states])
    #     print("夹爪位置:  ", ctrl.get_gripper_state().position)

    #     # 插值运动到目标
    #     ctrl.arm_control(positions=TARGET, duration=2.0)

    #     # 固定期间也可控制夹爪（需在外部循环中交替发帧，或用线程）
    #     ctrl.gripper_control(pos=-0.01, duration=1.0)

    #     ctrl.refresh_arm()
    #     states = ctrl.get_arm_states()
    #     print("关节角:", [f"{s.position:.3f}" for s in states])
    #     print("夹爪位置:  ", ctrl.get_gripper_state().position)

    # finally:
    #     ctrl.disable()
    #     ctrl.close()

    # ---- 双臂示例 ----
    # ctrl = XArmController(left_channel="can0", right_channel="can1")
    # ctrl.enable()
    # ctrl.refresh_arm()
    #
    # # 双臂同步运动到同一目标
    # ctrl.arm_control([0.0]*7, kp=200, kd=3, duration=2.0)
    #
    # # 双臂运动到不同目标（并行执行）
    # ctrl.arm_control(
    #     positions={"left": [0.1]*7, "right": [-0.1]*7},
    #     kp=200, kd=3, duration=2.0,
    # )
    #
    # ctrl.disable()
    # ctrl.close()