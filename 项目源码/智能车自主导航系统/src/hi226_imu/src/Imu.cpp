#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <eigen3/Eigen/Geometry>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <string>
#include <chrono>
#include "hi226_imu/packet.h"
#include "hi226_imu/imu_data_decode.h"

using namespace std::chrono_literals;

class Hi226ImuNode : public rclcpp::Node {
public:
    Hi226ImuNode() : Node("hi226_imu") {
        this->declare_parameter<std::string>("port", "/dev/imu");
        this->declare_parameter<std::string>("model", "hi226");
        this->declare_parameter<int>("baud", 115200);
        this->declare_parameter<std::string>("frame_id", "IMU_link");

        port_ = this->get_parameter("port").as_string();
        model_ = this->get_parameter("model").as_string();
        baud_ = this->get_parameter("baud").as_int();
        frame_id_ = this->get_parameter("frame_id").as_string();

        RCLCPP_INFO(this->get_logger(), "Model set to %s", model_.c_str());
        RCLCPP_INFO(this->get_logger(), "Baudrate set to %d", baud_);

        pub_ = this->create_publisher<sensor_msgs::msg::Imu>("/imu_data", 10);

        fd_ = open(port_.c_str(), O_RDWR);
        if (fd_ < 0) {
            RCLCPP_ERROR(this->get_logger(), "Port Error!: %s", port_.c_str());
            throw std::runtime_error("Failed to open serial port");
        }

        uart_set(fd_, baud_, 0, 8, 'N', 1);

        imu_data_decode_init();

        timer_ = this->create_wall_timer(10ms, std::bind(&Hi226ImuNode::read_and_publish, this));
    }

    ~Hi226ImuNode() {
        if (fd_ >= 0) {
            ::close(fd_);
        }
    }

private:
    void read_and_publish() {
        uint8_t buf[41];
        ssize_t n = read(fd_, buf, sizeof(buf));
        for (ssize_t i = 0; i < n; i++) {
            Packet_Decode(buf[i]);
        }

        int16_t Acc[3] = {0};
        int16_t Gyo[3] = {0};
        int16_t Mag[3] = {0};
        float Eular[3] = {0};
        uint8_t ID = 0;

        get_raw_acc(Acc);
        get_raw_gyo(Gyo);
        get_raw_mag(Mag);
        get_eular(Eular);
        get_id(&ID);

        Eigen::Vector3d ea0(Eular[1] * M_PI / 180.0,
                            Eular[0] * M_PI / 180.0,
                            Eular[2] * M_PI / 180.0);
        Eigen::Matrix3d R;
        R = Eigen::AngleAxisd(ea0[0], Eigen::Vector3d::UnitX())
            * Eigen::AngleAxisd(ea0[1], Eigen::Vector3d::UnitY())
            * Eigen::AngleAxisd(ea0[2], Eigen::Vector3d::UnitZ());
        Eigen::Quaterniond q;
        q = R;

        auto msg = sensor_msgs::msg::Imu();
        msg.header.stamp = this->now();
        msg.header.frame_id = frame_id_;
        msg.orientation.w = q.w();
        msg.orientation.x = q.x();
        msg.orientation.y = q.y();
        msg.orientation.z = q.z();
        msg.linear_acceleration.x = Acc[0] * 1e-3 * 9.81;
        msg.linear_acceleration.y = Acc[1] * 1e-3 * 9.81;
        msg.linear_acceleration.z = Acc[2] * 1e-3 * 9.81;

        pub_->publish(msg);
    }

    int uart_set(int fd, int baude, int c_flow, int bits, char parity, int stop) {
        struct termios options;
        if(tcgetattr(fd, &options) < 0) {
            perror("tcgetattr error");
            return -1;
        }
        cfsetispeed(&options,B115200);
        cfsetospeed(&options,B115200);
        options.c_cflag |= CLOCAL;
        options.c_cflag |= CREAD;
        switch(c_flow) {
            case 0: options.c_cflag &= ~CRTSCTS; break;
            case 1: options.c_cflag |= CRTSCTS; break;
            case 2: options.c_cflag |= IXON|IXOFF|IXANY; break;
            default: return -1;
        }
        switch(bits) {
            case 5: options.c_cflag &= ~CSIZE; options.c_cflag |= CS5; break;
            case 6: options.c_cflag &= ~CSIZE; options.c_cflag |= CS6; break;
            case 7: options.c_cflag &= ~CSIZE; options.c_cflag |= CS7; break;
            case 8: options.c_cflag &= ~CSIZE; options.c_cflag |= CS8; break;
            default: return -1;
        }
        switch(parity) {
            case 'n': case 'N': options.c_cflag &= ~PARENB; options.c_cflag &= ~INPCK; break;
            case 's': case 'S': options.c_cflag &= ~PARENB; options.c_cflag &= ~CSTOPB; break;
            case 'o': case 'O': options.c_cflag |= PARENB; options.c_cflag |= PARODD; options.c_cflag |= INPCK; options.c_cflag |= ISTRIP; break;
            case 'e': case 'E': options.c_cflag |= PARENB; options.c_cflag &= ~PARODD; options.c_cflag |= INPCK; options.c_cflag |= ISTRIP; break;
            default: return -1;
        }
        switch(stop) {
            case 1: options.c_cflag &= ~CSTOPB; break;
            case 2: options.c_cflag |= CSTOPB; break;
            default: return -1;
        }
        options.c_oflag &= ~OPOST;
        options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
        options.c_cc[VTIME] = 0;
        options.c_cc[VMIN] = 1;
        tcflush(fd,TCIFLUSH);
        if(tcsetattr(fd,TCSANOW,&options) < 0) {
            perror("tcsetattr failed");
            return -1;
        }
        return 0;
    }

    std::string port_, model_, frame_id_;
    int baud_;
    int fd_;
    rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<Hi226ImuNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}