/********************/
/* CLASS DEFINITION */
/********************/
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/point.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <visualization_msgs/msg/marker.hpp>

// 修改：继承自 rclcpp::Node
class L1Controller : public rclcpp::Node
{
    public:
        L1Controller();
        void initMarker();
        bool isForwardWayPt(const geometry_msgs::msg::Point& wayPt, const geometry_msgs::msg::Pose& carPose);
        bool isWayPtAwayFromLfwDist(const geometry_msgs::msg::Point& wayPt, const geometry_msgs::msg::Point& car_pos);
        double getYawFromPose(const geometry_msgs::msg::Pose& carPose);        
        double getEta(const geometry_msgs::msg::Pose& carPose);
        double getCar2GoalDist();
        double getL1Distance(const double& _Vcmd);
        double getSteeringAngle(double eta);
        double getGasInput(const float& current_v);
        geometry_msgs::msg::Point get_odom_car2WayPtVec(const geometry_msgs::msg::Pose& carPose);
        void PID_init();

    private:
        // 修改：移除 node_ 指针，因为现在直接继承Node
        struct PID *speed_pid;
        
        // 修改：使用正确的消息类型
        rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub;
        rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr path_sub;
        rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr goal_sub;
        rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
        rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr marker_pub;
        rclcpp::TimerBase::SharedPtr timer1;
        rclcpp::TimerBase::SharedPtr timer2;
        
        visualization_msgs::msg::Marker points, line_strip, goal_circle;
        geometry_msgs::msg::Twist cmd_vel;
        geometry_msgs::msg::Point odom_goal_pos;
        nav_msgs::msg::Odometry odom;
        nav_msgs::msg::Path map_path, odom_path;
        double L, Lfw, Lrv, Vcmd, lfw, lrv, steering, u, v;
        double Gas_gain, baseAngle, Angle_gain, goalRadius;
        int controller_freq, baseSpeed;
        bool foundForwardPt, goal_received, goal_reached;
        int car_stop;
        
        void odomCB(const nav_msgs::msg::Odometry::SharedPtr odomMsg);
        void pathCB(const nav_msgs::msg::Path::SharedPtr pathMsg);
        void goalCB(const geometry_msgs::msg::PoseStamped::SharedPtr goalMsg);
        void goalReachingCB();
        void controlLoopCB();

}; // end of class