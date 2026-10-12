//subscriber imu specifcation data package
#include <rclcpp/rclcpp.hpp>
#include <iostream>
#include <sensor_msgs/msg/imu.hpp>


int main(int argc, char **argv)
{
	rclcpp::init(argc, argv);
	auto node = rclcpp::Node::make_shared("sub_spec");
	execlp("rostopic", "rostopic", "echo", "/imu_data",NULL);

	rclcpp::spin(node);
	rclcpp::shutdown();
}
