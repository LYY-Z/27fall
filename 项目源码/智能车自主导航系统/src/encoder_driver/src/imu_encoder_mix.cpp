#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "message_filters/subscriber.h"
#include "message_filters/synchronizer.h"
#include "message_filters/sync_policies/approximate_time.h"

class EncoderImuMixNode : public rclcpp::Node
{
public:
    EncoderImuMixNode() : Node("encoder_imu_mix")
    {
        encoder_imu_pub_ = this->create_publisher<nav_msgs::msg::Odometry>(
            "/encoder_imu_odom", 10);
        
        // 初始化订阅器
        imu_sub_.subscribe(this, "/imu_data");
        encoder_sub_.subscribe(this, "/encoder");
        
        // 设置同步器
        sync_.reset(new message_filters::Synchronizer<SyncPolicy>(
            SyncPolicy(10), imu_sub_, encoder_sub_));
        sync_->registerCallback(&EncoderImuMixNode::callback, this);
        
        RCLCPP_INFO(this->get_logger(), "节点启动成功");
    }

private:
    void callback(const sensor_msgs::msg::Imu::ConstSharedPtr& imu_data,
                  const nav_msgs::msg::Odometry::ConstSharedPtr& speed)
    {
        auto fused_odom = nav_msgs::msg::Odometry();
        fused_odom.header = imu_data->header;
        fused_odom.header.frame_id = "odom";
        fused_odom.child_frame_id = "base_link";
        fused_odom.pose.pose.orientation = imu_data->orientation;
        fused_odom.twist = speed->twist;
        
        encoder_imu_pub_->publish(fused_odom);
    }

    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr encoder_imu_pub_;
    message_filters::Subscriber<sensor_msgs::msg::Imu> imu_sub_;
    message_filters::Subscriber<nav_msgs::msg::Odometry> encoder_sub_;
    
    using SyncPolicy = message_filters::sync_policies::ApproximateTime<
        sensor_msgs::msg::Imu, nav_msgs::msg::Odometry>;
    std::shared_ptr<message_filters::Synchronizer<SyncPolicy>> sync_;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<EncoderImuMixNode>());
    rclcpp::shutdown();
    return 0;
}