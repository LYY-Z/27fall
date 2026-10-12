import signal
import time
import sys
import os
import numpy as np
from scipy.spatial.transform import Rotation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from XArmcontroller import XArmController, ARM_7DOF_LIMITS, MITParam
from gravity_comp import ArmDynamics, move_to_initial_position
import pinocchio as pin

URDF_PATH = "/home/lft-vlai2/damiao_python/xarm_description/urdf/robot/xarm_bimanual.urdf"

class RobotHardware:

    _KD = [0.5, 3.0, 0.1, 0.1, 0.1, 0.2, 0.2]

    def __init__(self, can_channel: str = "can0"):
        print(f"[硬件] 连接机械臂，CAN 接口: {can_channel}")
        self._channel = can_channel
        self._n_joints = 7

        self._ctrl = XArmController({can_channel: ARM_7DOF_LIMITS})
        self._ctrl.enable_all()

        self._ctrl.recv_all(channel=can_channel, timeout=0.1)
        print(f"[硬件] 机械臂已使能，关节数: {self._n_joints}")

    def get_motor_count(self) -> int:
        return self._n_joints

    def read_joint_state(self):
        q  = np.array(self._ctrl.get_positions(self._channel))
        dq = np.array(self._ctrl.get_velocities(self._channel))
        return q, dq

    def send_torque(self, tau: np.ndarray):
        params = [
            MITParam(kp=0.0, kd=self._KD[i], q=0.0, dq=0.0, tau=float(tau[i]))
            for i in range(self._n_joints)
        ]
        self._ctrl.mit_control_all(self._channel, params)
        self._ctrl.recv_all(channel=self._channel, timeout=0.01)

    def disable(self):
        self._ctrl.disable_all()
        self._ctrl.recv_all(channel=self._channel, timeout=0.05)
        self._ctrl.close()

def compute_gravity_compensation(model, data, q: np.ndarray) -> np.ndarray:

    v_zero = np.zeros(model.nv)
    a_zero = np.zeros(model.nv)
    tau_g = pin.rnea(model, data, q, v_zero, a_zero)
    return tau_g.copy()

def compute_orientation_error(R_des: np.ndarray, R_cur: np.ndarray) -> np.ndarray:
    R_err = R_cur.T @ R_des
    error_local = Rotation.from_matrix(R_err).as_rotvec()
    return R_cur @ error_local

def rotation_matrix_to_euler_zyx(R: np.ndarray) -> np.ndarray:
    return Rotation.from_matrix(R).as_euler('xyz')

def clip_torque(torque: np.ndarray, max_torque: np.ndarray) -> np.ndarray:
    return np.clip(torque, -max_torque, max_torque)

keep_running = True

def signal_handler(sig, frame):
    global keep_running
    keep_running = False
    print("\n\n程序被中断")

signal.signal(signal.SIGINT, signal_handler)

def main():
  
    can_channel = sys.argv[1] if len(sys.argv) > 1 else "can0"
    arm_side    = sys.argv[2] if len(sys.argv) > 2 else "right"
    arm_prefix  = f"xarm_{arm_side}_"

    robot = RobotHardware(can_channel)

    if not os.path.exists(URDF_PATH):
        print(f"[ERROR] URDF 文件未找到: {URDF_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"正在加载 URDF 模型（单臂，prefix='{arm_prefix}'）...")
    arm_dyn = ArmDynamics(URDF_PATH, arm_prefix)
    model   = arm_dyn.model
    data    = arm_dyn.data

    print(f"URDF 模型加载成功: {URDF_PATH}")
    print(f"模型包含 {model.njoints - 1} 个关节（不含 base）")
    print(f"模型自由度 nq = {model.nq}, nv = {model.nv}")

    num_arm_joints = robot.get_motor_count()
    print(f"机械臂可控关节数: {num_arm_joints}")

    ee_frame_id = None
    for fid in range(model.nframes):
        if "link7" in model.frames[fid].name.lower():
            ee_frame_id = fid
    if ee_frame_id is None:
        for fid in reversed(range(model.nframes)):
            if model.frames[fid].name not in ("universe", "world"):
                ee_frame_id = fid
                break
    if ee_frame_id is None:
        raise RuntimeError("未找到有效的末端执行器 frame，请检查 URDF 模型")

    ee_frame_name = model.frames[ee_frame_id].name
    print(f"末端执行器 frame: '{ee_frame_name}'  (ID: {ee_frame_id})")

    K_cartesian = np.array([
        200.0, 200.0, 200.0,
          4.0,   4.0,   4.0,
    ])

    B_cartesian = np.array([
        2.0, 2.0, 2.0,
        0.05, 0.05, 0.05,
    ])

    tau_limit = np.array([54.0, 54.0, 28.0, 28.0, 10.0, 10.0, 10.0])

    print("\n正在移动到初始位置（约 2.2 秒）...")
    move_to_initial_position(robot._ctrl, can_channel)
    print("已到达初始位置。\n")

    print("正在计算期望末端位置...")

    q_des_joint = np.array([-0.049, 0.53, -0.3313, 1.272, 0.521, 0.05855, 0.605])

    pin.forwardKinematics(model, data, q_des_joint)
    pin.updateFramePlacements(model, data)

    ee_pose = data.oMf[ee_frame_id]
    x_des   = ee_pose.translation.copy()
    R_des   = ee_pose.rotation.copy()

    euler_des = rotation_matrix_to_euler_zyx(R_des)
    print(f"期望末端位置 (m):     {np.round(x_des, 4)}")
    print(f"期望末端姿态 (rad):   {np.round(euler_des, 4)}")

    G_init = compute_gravity_compensation(model, data, q_des_joint)
    print(f"\n初始重力补偿力矩 (Nm): {np.round(G_init[:num_arm_joints], 3)}")

    print("\n" + "=" * 60)
    print("笛卡尔空间阻抗控制（带重力补偿）")
    print("=" * 60)
    print(f"CAN 接口: {can_channel}  |  手臂: {arm_side}")
    print(f"位置刚度 K_pos (N/m):      {K_cartesian[:3]}")
    print(f"姿态刚度 K_ori (Nm/rad):   {K_cartesian[3:]}")
    print(f"线速度阻尼 B_vel (N·s/m):  {B_cartesian[:3]}")
    print(f"角速度阻尼 B_ω (Nm·s/rad): {B_cartesian[3:]}")
    print("\n提示：")
    print("  - 机械臂末端将保持期望位置，可手动推动感受阻抗效果")
    print("  - 推动后松开，机械臂会回到期望位置")
    print("  - 按 Ctrl+C 退出")
    print("  - 结束后电机会自动掉电，注意安全！")
    print("=" * 60 + "\n")

    time.sleep(1)

    dt              = 0.005
    print_interval  = 0.5
    last_print_time = time.time()
    max_ori_error   = 0.5

    dq_alpha    = 0.05
    dq_filtered = np.zeros(num_arm_joints)

    tau_rate_limit = 5.0
    tau_prev       = np.zeros(num_arm_joints)

    try:
        while keep_running:
            t0 = time.perf_counter()

            q_current, v_current = robot.read_joint_state()

            dq_filtered = dq_alpha * v_current + (1.0 - dq_alpha) * dq_filtered

            pin.forwardKinematics(model, data, q_current, dq_filtered)
            pin.updateFramePlacements(model, data)

            J = pin.computeFrameJacobian(
                model, data, q_current, ee_frame_id,
                pin.LOCAL_WORLD_ALIGNED
            )

            ee_pose_current = data.oMf[ee_frame_id]
            x_current = ee_pose_current.translation.copy()
            R_current = ee_pose_current.rotation.copy()

            v_ee = J @ dq_filtered

            pos_error = x_des - x_current
            ori_error = compute_orientation_error(R_des, R_current)

            ori_norm = np.linalg.norm(ori_error)
            if ori_norm > max_ori_error:
                ori_error = ori_error / ori_norm * max_ori_error

            x_error = np.concatenate([pos_error, ori_error])

            F_cartesian = K_cartesian * x_error - B_cartesian * v_ee

            tau_impedance = J.T @ F_cartesian

            G = compute_gravity_compensation(model, data, q_current)

            tor_total = tau_impedance[:num_arm_joints] + G[:num_arm_joints]

            tor_total = clip_torque(tor_total, tau_limit)
            delta     = np.clip(tor_total - tau_prev, -tau_rate_limit, tau_rate_limit)
            tor_total = np.clip(tau_prev + delta, -tau_limit, tau_limit)
            tau_prev  = tor_total.copy()
            robot.send_torque(tor_total)
            now = time.time()
            if now - last_print_time >= print_interval:
                euler_cur = rotation_matrix_to_euler_zyx(R_current)
                print(f"\n当前末端位置 (m):   {np.round(x_current, 4)}")
                print(f"位置误差 (m):       {np.round(pos_error, 4)}")
                print(f"当前末端姿态 (rad): {np.round(euler_cur, 4)}")
                print(f"姿态误差 (rad):     {np.round(ori_error, 4)}")
                print(f"笛卡尔力/力矩:      {np.round(F_cartesian, 3)}")
                print(f"关节力矩 (Nm):      {np.round(tor_total, 3)}")
                last_print_time = now

            elapsed = time.perf_counter() - t0
            sleep_t = dt - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

    finally:
        print("\n正在停机，失能所有电机...")
        robot.disable()
        print("所有电机已停止")

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
