//
//racecar
//

#include "../include/racecar_driver.h"
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/rclcpp.hpp>
#include <ament_index_cpp/get_package_share_directory.hpp>
#include <geometry_msgs/msg/twist.hpp>

void TwistCallback(const geometry_msgs::msg::Twist& twist)
{
    double angle;
    //RCLCPP_INFO("x= %f", twist.linear.x);
    //RCLCPP_INFO("z= %f", twist.angular.z);
    angle = 2500.0 - twist.angular.z * 2000.0 / 180.0;
    //RCLCPP_INFO("angle= %d",uint16_t(angle));
    send_cmd(uint16_t(twist.linear.x),uint16_t(angle));
}

int main(int argc, char** argv)
{
    //char data[] = "/dev/ttyUSB3";
    char data[] = "/dev/car";
    art_racecar_init(38400,data);
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("racecar_driver");

    auto sub = node->create_subscription<geometry_msgs::msg::Twist>(
        "/car/cmd_vel", 1, TwistCallback);

    rclcpp::spin(node);
    rclcpp::shutdown();
}
