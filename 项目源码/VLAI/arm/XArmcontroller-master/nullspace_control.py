import os
import signal
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import List

import numpy as np
import pinocchio as pin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from XArmcontroller import XArmController, MITParam, ARM_7DOF_LIMITS
from gravity_comp import (
    ArmDynamics, GRAVITY_SCALE,
    compute_friction, _Fc, _k, _Fv, _Fo,
    CORIOLIS_GAIN, FRICTION_GAIN,
    move_to_initial_position,
)
RIGHT_KD = [0.5, 0.5, 0.1, 0.1, 0.1, 0.2, 4.2]
_stop = threading.Event()
signal.signal(signal.SIGINT,  lambda *_: _stop.set())
signal.signal(signal.SIGTERM, lambda *_: _stop.set())

@dataclass
class Config:
    urdf_path: str = "/home/lft-vlai2/damiao_python/xarm_description/urdf/robot/xarm_bimanual.urdf"
    right_can: str = "can0"
    left_can:  str = "can1"
    n_joints:  int = 7
    target_dt: float = 0.002

    ee_kp_pos: float = 450.0
    ee_kp_ori: float = 40.0

    sigma_high:     float = 0.12
    sigma_low:      float = 0.03
    gain_min_ratio: float = 0.35

    kd_joint: np.ndarray = field(
        default_factory=lambda: np.array([0.12, 0.12, 0.08, 0.08, 0.04, 0.04, 0.02])
    )
    null_kd: float = 0.008

    lambda_pinv:      float = 0.03
    lambda_null_base: float = 0.015
    lambda_null_min:  float = 0.10
    lambda_null_max:  float = 0.60

    tau_rate_limit: float = 8.0
    tau_max:        float = 25.0

    dq_alpha: float = 0.15

    sigma_warn_low: float = 0.05
    sigma_warn_mid: float = 0.10

class NullSpaceCtrl:

    def __init__(self, cfg: Config, prefix: str):
        self.cfg = cfg
        self.N   = cfg.n_joints

        self._dyn = ArmDynamics(cfg.urdf_path, prefix)
        self.model = self._dyn.model
        self.data  = self._dyn.data
        self.ee_id = self._find_ee_frame()

        self.x0: np.ndarray = np.zeros(3)
        self.R0: np.ndarray = np.eye(3)

        self._dq_filt: np.ndarray | None = None

        self._tau_prev = np.zeros(self.N)

        print(f"[NullSpaceCtrl] EE frame: '{self.model.frames[self.ee_id].name}', "
              f"nq={self.model.nq}")

    def _find_ee_frame(self) -> int:
        hits = [fid for fid in range(self.model.nframes)
                if "link7" in self.model.frames[fid].name.lower()]
        if hits:
            return hits[-1]
        for fid in reversed(range(self.model.nframes)):
            if self.model.frames[fid].name not in ("universe", "world"):
                return fid
        return self.model.nframes - 1

    def set_target(self, q: np.ndarray):
        T = self._fk(q)
        self.x0 = T.translation.copy()
        self.R0 = T.rotation.copy()

    def compute(self, q: np.ndarray, dq_raw: np.ndarray) -> np.ndarray:
        cfg = self.cfg
        dq  = self._filter_dq(dq_raw)

        tau_ff = self._feedforward(q, dq)

        T_cur = self._fk(q)
        x_cur = T_cur.translation.copy()
        R_cur = T_cur.rotation.copy()
        J     = self._jacobian(q)
        U, s, Vt = np.linalg.svd(J, full_matrices=False)
        sigma_min = float(s[-1])

        lambda_null = np.clip(
            cfg.lambda_null_base / max(sigma_min, 1e-4),
            cfg.lambda_null_min, cfg.lambda_null_max,
        )
        gain_scale = self._sigma_gain(sigma_min)
        kp_pos = cfg.ee_kp_pos * gain_scale
        kp_ori = cfg.ee_kp_ori * gain_scale

        J_null = self._dls_pinv(U, s, Vt, lambda_null)
        N      = np.eye(self.N) - J_null @ J

        e_pos  = self.x0 - x_cur
        e_ori  = pin.log3(self.R0 @ R_cur.T)
        f_ee   = np.concatenate([kp_pos * e_pos, kp_ori * e_ori])
        tau_main = J.T @ f_ee

        tau_damp = -cfg.kd_joint * dq
        tau_null = N @ (-cfg.null_kd * dq)

  
        tau_des = tau_ff + tau_main + tau_damp + tau_null
        tau_out = self._safe_limit(tau_des)

        self._diag = {
            "sigma_min": sigma_min,
            "gain_scale": gain_scale,
            "kp_pos": kp_pos,
            "lambda_null": lambda_null,
            "pos_err_mm": np.linalg.norm(e_pos) * 1000,
            "ori_err_deg": np.linalg.norm(e_ori) * 180 / np.pi,
            "norm_ff": np.linalg.norm(tau_ff),
            "norm_main": np.linalg.norm(tau_main),
            "norm_damp": np.linalg.norm(tau_damp),
            "norm_null": np.linalg.norm(tau_null),
        }

        return tau_out

    def get_diag(self) -> dict:
        return getattr(self, "_diag", {})

    def ramp_down_tau(self) -> np.ndarray:
        self._tau_prev *= 0.85
        return self._tau_prev.copy()
    def _fk(self, q: np.ndarray) -> pin.SE3:
        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)
        return self.data.oMf[self.ee_id]

    def _jacobian(self, q: np.ndarray) -> np.ndarray:
        return pin.computeFrameJacobian(
            self.model, self.data, q, self.ee_id,
            pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
        )

    def _feedforward(self, q: np.ndarray, dq: np.ndarray) -> np.ndarray:
        g   = self._dyn.get_gravity(q) * GRAVITY_SCALE
        cor = self._dyn.get_coriolis(q, dq) * CORIOLIS_GAIN
        fri = np.array([
            compute_friction(dq[i], _Fc[i], _k[i], _Fv[i], _Fo[i])
            for i in range(self.N)
        ]) * FRICTION_GAIN
        return g + cor + fri

    def _filter_dq(self, dq_raw: np.ndarray) -> np.ndarray:
        a = self.cfg.dq_alpha
        if self._dq_filt is None:
            self._dq_filt = dq_raw.copy()
        else:
            self._dq_filt = a * dq_raw + (1 - a) * self._dq_filt
        return self._dq_filt.copy()

    def _sigma_gain(self, sigma_min: float) -> float:
        cfg = self.cfg
        if sigma_min >= cfg.sigma_high:
            return 1.0
        if sigma_min <= cfg.sigma_low:
            return cfg.gain_min_ratio
        return cfg.gain_min_ratio + (1.0 - cfg.gain_min_ratio) * \
            (sigma_min - cfg.sigma_low) / (cfg.sigma_high - cfg.sigma_low)

    @staticmethod
    def _dls_pinv(U, s, Vt, lam: float) -> np.ndarray:
        return Vt.T @ np.diag(s / (s**2 + lam**2)) @ U.T

    def _safe_limit(self, tau_des: np.ndarray) -> np.ndarray:
        cfg = self.cfg
        delta = np.clip(tau_des - self._tau_prev, -cfg.tau_rate_limit, cfg.tau_rate_limit)
        tau   = np.clip(self._tau_prev + delta, -cfg.tau_max, cfg.tau_max)
        self._tau_prev = tau.copy()
        return tau

    def diagnose(self, q: np.ndarray):
        T = self._fk(q)
        J = self._jacobian(q)
        _, s, _ = np.linalg.svd(J, full_matrices=False)
        sm = float(s[-1])
        label = "良好" if sm > self.cfg.sigma_warn_mid else \
                "偏低" if sm > self.cfg.sigma_warn_low else "过低!"
        print(f"[诊断] 末端={T.translation.round(4)}, σ_min={sm:.4f}({label}), "
              f"奇异值={[f'{v:.4f}' for v in s]}")

def run(mode: str = "right") -> None:
    cfg    = Config()
    can_ch = cfg.right_can if mode == "right" else cfg.left_can
    prefix = "xarm_right_" if mode == "right" else "xarm_left_"
    kd_arm = RIGHT_KD if mode == "right" else [0.2] * 7

    print(f"=== 零空间控制 · {mode} arm ({can_ch}) ===")
    if not os.path.exists(cfg.urdf_path):
        print(f"[ERROR] URDF 未找到: {cfg.urdf_path}", file=sys.stderr)
        sys.exit(1)

    ns_ctrl = NullSpaceCtrl(cfg, prefix)
    hw      = XArmController({can_ch: ARM_7DOF_LIMITS})
    N       = cfg.n_joints

    try:
        hw.enable_all()
        hw.recv_all(timeout=0.05)
        move_to_initial_position(hw, can_ch)

        q0 = np.array(hw.get_positions(can_ch)[:N])
        ns_ctrl.diagnose(q0)
        ns_ctrl.set_target(q0)

        print(f"[启动] 推动关节，末端保持不动；Ctrl+C 退出\n")

        frame_count = 0
        t_start = t_loop = t_print = time.monotonic()

        while not _stop.is_set():

            now = time.monotonic()
            sleep_t = cfg.target_dt - (now - t_loop)
            if sleep_t > 0:
                time.sleep(sleep_t)
            t_loop = time.monotonic()
            frame_count += 1

            q      = np.array(hw.get_positions(can_ch)[:N])
            dq_raw = np.array(hw.get_velocities(can_ch)[:N])
            tau    = ns_ctrl.compute(q, dq_raw)

            params = [
                MITParam(kp=0.0, kd=float(kd_arm[i]), q=0.0, dq=0.0, tau=float(tau[i]))
                for i in range(N)
            ]
            hw.mit_control_all(can_ch, params)
            hw.recv_all(channel=can_ch)

            t_now = time.monotonic()
            if t_now - t_print >= 1.0:
                hz = frame_count / (t_now - t_start)
                d  = ns_ctrl.get_diag()
                sm = d.get("sigma_min", 0)
                label = "良好" if sm > cfg.sigma_warn_mid else \
                        "偏低" if sm > cfg.sigma_warn_low else "过低!"
                print(
                    f"  {hz:.0f}Hz"
                    f" | pos={d.get('pos_err_mm',0):.1f}mm"
                    f" ori={d.get('ori_err_deg',0):.1f}°"
                    f" | σ={sm:.3f}[{label}]"
                    f" s={d.get('gain_scale',0):.2f}"
                    f" | τ: ff={d.get('norm_ff',0):.1f}"
                    f" main={d.get('norm_main',0):.1f}"
                    f" damp={d.get('norm_damp',0):.1f}"
                    f" null={d.get('norm_null',0):.2f}"
                )
                t_print = t_now

    finally:
        _stop.set()
        print("[停止] 力矩渐降中...")
        for _ in range(60):
            tau = ns_ctrl.ramp_down_tau()
            params = [
                MITParam(kp=0.0, kd=float(kd_arm[i]), q=0.0, dq=0.0, tau=float(tau[i]))
                for i in range(N)
            ]
            hw.mit_control_all(can_ch, params)
            hw.recv_all(channel=can_ch)
            time.sleep(0.01)
        hw.disable_all()
        hw.recv_all(timeout=0.05)
        hw.close()
        print("=== 已停止 ===")

if __name__ == "__main__":
    mode = "right"
    if len(sys.argv) >= 2:
        mode = sys.argv[1].lower()
        if mode not in ("right", "left"):
            print("用法: python null_space_ctrl_v2.py [right|left]")
            sys.exit(1)
    run(mode)
