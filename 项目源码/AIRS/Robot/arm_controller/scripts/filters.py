from sensor_msgs.msg import Imu, JointState
from geometry_msgs.msg import Pose2D, Twist
import math


class LowPassFilter:
    """
    First-order IIR low-pass filter for real-time signal processing.
    """
    def __init__(self, cutoff_freq: float, sampling_freq: float):
        """
        :param cutoff_freq: Cutoff frequency in Hz.
        :param sampling_freq: Sampling frequency in Hz.
        """
        dt = 1.0 / sampling_freq
        tau = 1.0 / (2 * math.pi * cutoff_freq)
        self.alpha = dt / (dt + tau)
        self.y = 0.0  # filtered output

    def update(self, x: float) -> float:
        """
        Update filter with new raw value.
        :param x: Raw input value.
        :return: Filtered output.
        """
        self.y = self.alpha * x + (1.0 - self.alpha) * self.y
        return self.y

    def reset(self, value: float = 0.0):
        """Reset filter state."""
        self.y = value


class JointStateFilter:
    """
    Applies low-pass filtering to wheel state measurements.
    """
    def __init__(
        self,
        size: int=3,
        pos_cutoff: float=None,
        vel_cutoff: float=None,
        eff_cutoff: float=None,
        sampling_freq: float=100.0
    ):
        """
        :param size: Number of wheel joints.
        :param pos_cutoff: Cutoff frequency for position measurement (Hz).
        :param vel_cutoff: Cutoff frequency for velocity measurement (Hz).
        :param eff_cutoff: Cutoff frequency for effort measurement (Hz).
        :param sampling_freq: Wheel state sampling frequency (Hz).
        """
        # Initialize filters for each axis
        self.size = size
        if pos_cutoff:
            self.pos_filters = [LowPassFilter(pos_cutoff, sampling_freq) for _ in range(self.size)]
        else:
            self.pos_filters = None

        if vel_cutoff:
            self.vel_filters = [LowPassFilter(vel_cutoff, sampling_freq) for _ in range(self.size)]
        else:
            self.vel_filters = None

        if eff_cutoff:
            self.eff_filters = [LowPassFilter(eff_cutoff, sampling_freq) for _ in range(self.size)]
        else:
            self.eff_filters = None

        self.filtered_msg = JointState()

    def filter_joint_state(self, raw_msg: JointState) -> JointState:
        """
        Apply filtering to raw JointState message and return a new filtered JointState message.
        """
        self.filtered_msg = JointState()
        self.filtered_msg.name = raw_msg.name
        self.filtered_msg.header = raw_msg.header

        # Filter position
        if self.pos_filters:
            self.filtered_msg.position = [self.pos_filters[i].update(raw_msg.position[i]) for i in range(self.size)]
        else:
            self.filtered_msg.position = raw_msg.position

        # Filter velocity
        if self.vel_filters:
            self.filtered_msg.velocity = [self.vel_filters[i].update(raw_msg.velocity[i]) for i in range(self.size)]
        else:
            self.filtered_msg.velocity = raw_msg.velocity

        # Filter effort
        if self.eff_filters:
            self.filtered_msg.effort = [self.eff_filters[i].update(raw_msg.effort[i]) for i in range(self.size)]
        else:
            self.filtered_msg.effort = raw_msg.effort

        return self.filtered_msg
    
    def reset(self):
        """Reset all filter states."""
        if self.pos_filters:
            for f in self.pos_filters:
                f.reset()
        if self.vel_filters:
            for f in self.vel_filters:
                f.reset()
        if self.eff_filters:
            for f in self.eff_filters:
                f.reset()


class Pose2DFilter:
    """
    Applies low-pass filtering to wheel state measurements.
    """
    def __init__(
        self,
        pos_cutoff: float=None,
        theta_cutoff: float=None,
        sampling_freq: float=100.0
    ):
        """
        :param pos_cutoff: Cutoff frequency for x, y measurement (Hz).
        :param theta_cutoff: Cutoff frequency for theta measurement (Hz).
        :param sampling_freq: Wheel state sampling frequency (Hz).
        """
        # Initialize filters for each axis
        if pos_cutoff:
            self.x_filters = LowPassFilter(pos_cutoff, sampling_freq)
            self.y_filters = LowPassFilter(pos_cutoff, sampling_freq)
        else:
            self.x_filters = None
            self.y_filters = None

        if theta_cutoff:
            self.theta_filters = LowPassFilter(theta_cutoff, sampling_freq)
        else:
            self.theta_filters = None

        self.filtered_msg = Pose2D()

    def filter_pose2d(self, raw_msg: Pose2D) -> Pose2D:
        """
        Apply filtering to raw Pose2D message and return a new filtered Pose2D message.
        """
        self.filtered_msg = Pose2D()

        # Filter position x and y
        if self.x_filters:
            self.filtered_msg.x = self.x_filters.update(raw_msg.x[i])
        else:
            self.filtered_msg.x = raw_msg.x

        if self.y_filters:
            self.filtered_msg.y = self.y_filters.update(raw_msg.y)
        else:
            self.filtered_msg.y = raw_msg.y

        # Filter theta
        if self.theta_filters:
            self.filtered_msg.theta = self.theta_filters.update(raw_msg.theta)
        else:
            self.filtered_msg.theta = raw_msg.theta

        return self.filtered_msg
    
    def reset(self):
        """Reset all filter states."""
        if self.x_filters:
            self.x_filters.reset()
        if self.y_filters:
            self.y_filters.reset()
        if self.theta_filters:
            self.theta_filters.reset()


class TwistFilter:
    """
    Applies low-pass filtering to wheel state measurements.
    """
    def __init__(
        self,
        linear_cutoff: float=None,
        angular_cutoff: float=None,
        sampling_freq: float=100.0
    ):
        """
        :param linear_cutoff: Cutoff frequency for linear measurement (Hz).
        :param angular_cutoff: Cutoff frequency for angular measurement (Hz).
        :param sampling_freq: Wheel state sampling frequency (Hz).
        """
        # Initialize filters for each axis
        if linear_cutoff:
            self.linear_filters = [LowPassFilter(linear_cutoff, sampling_freq) for _ in range(3)]
        else:
            self.linear_filters = None

        if angular_cutoff:
            self.angular_filters = [LowPassFilter(angular_cutoff, sampling_freq) for _ in range(3)]
        else:
            self.angular_filters = None

        self.filtered_msg = Twist()

    def filter_twist(self, raw_msg: Twist) -> Twist:
        """
        Apply filtering to raw Twist message and return a new filtered Twist message.
        """
        self.filtered_msg = Twist()

        # Filter linear
        if self.linear_filters:
            self.filtered_msg.linear.x = self.linear_filters[0].update(raw_msg.linear.x)
            self.filtered_msg.linear.y = self.linear_filters[1].update(raw_msg.linear.y)
            self.filtered_msg.linear.z = self.linear_filters[2].update(raw_msg.linear.z)
        else:
            self.filtered_msg.linear = raw_msg.linear

        # Filter angular
        if self.angular_filters:
            self.filtered_msg.angular.x = self.angular_filters[0].update(raw_msg.angular.x)
            self.filtered_msg.angular.y = self.angular_filters[1].update(raw_msg.angular.y)
            self.filtered_msg.angular.z = self.angular_filters[2].update(raw_msg.angular.z)
        else:
            self.filtered_msg.angular = raw_msg.angular

        return self.filtered_msg
    
    def reset(self):
        """Reset all filter states."""
        if self.linear_filters:
            for f in self.linear_filters:
                f.reset()
        if self.angular_filters:
            for f in self.angular_filters:
                f.reset()
                