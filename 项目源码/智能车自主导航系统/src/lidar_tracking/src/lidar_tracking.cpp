
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <math.h>
#include "Control.h"

#define freq 1440
#define pi_2 1.57
int speed=1880;
typedef struct
{
    double range;
    double theta;
}Point_polar;

typedef struct
{
    double x;
    double y;
}Point_rectangular;

Control::PID pid;
// 声明全局变量
static float low_pass_val = 0.0f;

void cal_point(double theta, double range, double& tmp_x, double& tmp_y)
{
    tmp_x = range * sin(theta);
    tmp_y = range * cos(theta);
}

class PubAndSub : public rclcpp::Node
{
    public:
        PubAndSub() : Node("laser_go")
        {
            pub_ = this->create_publisher<geometry_msgs::msg::Twist>("car/cmd_vel", 5);
            sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
                "/scan", 5, std::bind(&PubAndSub::callback, this, std::placeholders::_1));
        }
        void callback(const sensor_msgs::msg::LaserScan::SharedPtr laser)
        {
            char negetiveNum = 0, positiveNum = 0;
            int i = 0, j = 0, k = 0;
            double range = 0, error = 0, negetiveSum = 0, positiveSum = 0, theta = 0, tmp_x = 0, tmp_y = 0, angle = 0;
            int flag_jk = 0;
            auto twist = geometry_msgs::msg::Twist();
            Point_rectangular red_p[30] = { 0,0 };
            Point_rectangular blue_p[30] = { 0,0 };
            Point_rectangular* p = red_p;
            RCLCPP_INFO(this->get_logger(), "start:-------------------------------------\n");
            for (i = 1;i < freq /3; i++)
            {
                RCLCPP_INFO(this->get_logger(), "%f", laser->ranges[i]);
            }
            RCLCPP_INFO(this->get_logger(), "end:-------------------------------------\n");

            //error = pid.PIDIncremental(error);
            angle = pid.PIDPositional(error * 10);

            float temp = angle;
            // angle = 0.6*angle + 0.4*low_pass_val;
            low_pass_val = angle;
            //error *= 25.0;
            twist.angular.z = 85 + angle;
            twist.linear.x = speed;//???
            if (abs(angle) <= 10)
                twist.linear.x += 10;
            if (twist.angular.z > 180)
                twist.angular.z = 180;
            if (twist.angular.z < 0)
                twist.angular.z = 0;

            pub_->publish(twist);
            // RCLCPP_INFO(this->get_logger(), "angle:%.2f", angle);
        }
    private:
        rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
        rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
};


int main(int argc, char* argv[])
{
    pid.Init();
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PubAndSub>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}