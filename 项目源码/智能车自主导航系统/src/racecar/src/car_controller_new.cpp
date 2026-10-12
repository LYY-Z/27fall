/*
Copyright (c) 2017, ChanYuan KUO, YoRu LU,
latest editor: HaoChih, LIN
All rights reserved. (Hypha ROS Workshop)

This file is part of hypha_racecar package.

hypha_racecar is free software: you can redistribute it and/or modify
it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as published
by the Free Software Foundation, either version 3 of the License, or
any later version.

hypha_racecar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU LESSER GENERAL PUBLIC LICENSE for more details.

You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
along with hypha_racecar.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "nav_msgs/msg/path.hpp"
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include <iostream>
#include "nav_msgs/msg/odometry.hpp"
#include "tf2/transform_datatypes.h"
#include "tf2_ros/transform_listener.h"
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include "tf2_ros/buffer.h"
#include "visualization_msgs/msg/marker.hpp"
#include "rclcpp/rclcpp.hpp"
#include <cmath>
#include "std_msgs/msg/float64.hpp"
#include "std_msgs/msg/string.hpp"

#define PI 3.14159265358979

using namespace std::chrono_literals;

/********************/
/* CLASS DEFINITION */
/********************/
class L1Controller : public rclcpp::Node
{
public:
  L1Controller();
  void initMarker();
  bool isWayPtAwayFromLfwDist(const geometry_msgs::msg::Point &wayPt, const geometry_msgs::msg::Point &car_pos);
  bool isForwardWayPt(const geometry_msgs::msg::Point &wayPt, const geometry_msgs::msg::Pose &carPose);
  double getYawFromPose(const geometry_msgs::msg::Pose &carPose);
  double getEta(const geometry_msgs::msg::Pose &carPose);
  double getCar2GoalDist();
  double getL1Distance(const double &_Vcmd);
  double getSteeringAngle(double eta);
  geometry_msgs::msg::Point get_odom_car2WayPtVec(const geometry_msgs::msg::Pose &carPose);

private:
  // Parameters
  double L, Vcmd, lfw, lrv, Lrv;
  int controller_freq;
  double Angle_gain_p, Angle_gain_d, baseSpeed, baseAngle;
  double k_rou, vp_max_base, vp_min, goalRadius, Lfw;
  double slow_final, fast_final;
  bool all;
  
  // State variables
  double last_steeringangle;
  bool foundForwardPt, goal_received, goal_reached;
  double stop_flag;
  int mapPathNum;
  int stopIdx;
  double line_wight;
  double initbaseSpeed;
  double obs_flag;
  bool traffic_flag;
  bool movebase_flag;

  // ROS 2 components
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub;
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr path_sub;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr goal_sub;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr encoder_sub;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr final_goal_sub;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr line_sub;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr traffic_light_sub;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr vision_sub;
  
  rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr marker_pub;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_movebase;
  
  rclcpp::TimerBase::SharedPtr timer1;
  rclcpp::TimerBase::SharedPtr timer2;
  
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_;

  // Messages
  visualization_msgs::msg::Marker points, line_strip, goal_circle;
  geometry_msgs::msg::Twist cmd_vel;
  geometry_msgs::msg::Point odom_goal_pos;
  nav_msgs::msg::Odometry odom, encoder;
  nav_msgs::msg::Path map_path;

  // Callbacks
  void odomCB(const nav_msgs::msg::Odometry::SharedPtr odomMsg);
  void pathCB(const nav_msgs::msg::Path::SharedPtr pathMsg);
  void encoderCB(const nav_msgs::msg::Odometry::SharedPtr encoderMsg);
  void goalCB(const geometry_msgs::msg::PoseStamped::SharedPtr goalMsg);
  void goalReachingCB();
  void controlLoopCB();
  void stopCB(const std_msgs::msg::Float64::SharedPtr stopMsg);
  void lineCB(const std_msgs::msg::Float64::SharedPtr lineMsg);
  void lightCB(const std_msgs::msg::String::SharedPtr msg);
  void stateCB(const std_msgs::msg::String::SharedPtr msg);
  double isline(double line_wight);
};

L1Controller::L1Controller() : Node("art_car_controller")
{
  // Parameters declaration with default values
  this->declare_parameter("L", 0.335);
  this->declare_parameter("Vcmd", 1.0);
  this->declare_parameter("lfw", 0.1675);
  this->declare_parameter("lrv", 10.0);
  this->declare_parameter("Lrv", 10.0);
  this->declare_parameter("controller_freq", 30);
  this->declare_parameter("Angle_gain_p", -1.0);
  this->declare_parameter("Angle_gain_d", -0.0);
  this->declare_parameter("baseSpeed", 0.0);
  this->declare_parameter("baseAngle", 90.0);
  this->declare_parameter("k_rou", 0.0);
  this->declare_parameter("vp_max_base", 0.0);
  this->declare_parameter("vp_min", 0.0);
  this->declare_parameter("goalRadius", 0.2);
  this->declare_parameter("Lfw", 0.3);
  this->declare_parameter("slow_final", 0.8);
  this->declare_parameter("fast_final", 1.1);
  this->declare_parameter("all", false);

  // Get parameters
  this->get_parameter("L", L);
  this->get_parameter("Vcmd", Vcmd);
  this->get_parameter("lfw", lfw);
  this->get_parameter("lrv", lrv);
  this->get_parameter("Lrv", Lrv);
  this->get_parameter("controller_freq", controller_freq);
  this->get_parameter("Angle_gain_p", Angle_gain_p);
  this->get_parameter("Angle_gain_d", Angle_gain_d);
  this->get_parameter("baseSpeed", baseSpeed);
  this->get_parameter("baseAngle", baseAngle);
  this->get_parameter("k_rou", k_rou);
  this->get_parameter("vp_max_base", vp_max_base);
  this->get_parameter("vp_min", vp_min);
  this->get_parameter("goalRadius", goalRadius);
  this->get_parameter("Lfw", Lfw);
  this->get_parameter("slow_final", slow_final);
  this->get_parameter("fast_final", fast_final);
  this->get_parameter("all", all);

  initbaseSpeed = baseSpeed;
  
  // Initialize TF
  tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

  // Subscribers
  odom_sub = this->create_subscription<nav_msgs::msg::Odometry>(
      "/odometry/filtered", 1, std::bind(&L1Controller::odomCB, this, std::placeholders::_1));
  path_sub = this->create_subscription<nav_msgs::msg::Path>(
      "/move_base/NavfnROS/plan", 1, std::bind(&L1Controller::pathCB, this, std::placeholders::_1));
  goal_sub = this->create_subscription<geometry_msgs::msg::PoseStamped>(
      "/move_base_simple/goal", 1, std::bind(&L1Controller::goalCB, this, std::placeholders::_1));
  encoder_sub = this->create_subscription<nav_msgs::msg::Odometry>(
      "/encoder", 1, std::bind(&L1Controller::encoderCB, this, std::placeholders::_1));
  final_goal_sub = this->create_subscription<std_msgs::msg::Float64>(
      "/arrfinal", 1, std::bind(&L1Controller::stopCB, this, std::placeholders::_1));
  line_sub = this->create_subscription<std_msgs::msg::Float64>(
      "/line_wight", 1, std::bind(&L1Controller::lineCB, this, std::placeholders::_1));
  traffic_light_sub = this->create_subscription<std_msgs::msg::String>(
      "/light", 1, std::bind(&L1Controller::lightCB, this, std::placeholders::_1));
  vision_sub = this->create_subscription<std_msgs::msg::String>(
      "/state", 1, std::bind(&L1Controller::stateCB, this, std::placeholders::_1));

  // Publishers
  marker_pub = this->create_publisher<visualization_msgs::msg::Marker>("car_path", 10);
  pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/car/cmd_vel", 1);
  pub_movebase = this->create_publisher<geometry_msgs::msg::Twist>("/move_base_control", 1);

  // Timers
  timer1 = this->create_wall_timer(
      std::chrono::milliseconds(static_cast<int>(1000.0 / controller_freq)),
      std::bind(&L1Controller::controlLoopCB, this));
  timer2 = this->create_wall_timer(
      std::chrono::milliseconds(static_cast<int>(500.0 / controller_freq)),
      std::bind(&L1Controller::goalReachingCB, this));

  // Initialize variables
  foundForwardPt = false;
  goal_received = false;
  goal_reached = false;
  stop_flag = 0.0;
  stopIdx = 0;
  line_wight = 0.0;
  obs_flag = 0.0;
  traffic_flag = true;
  movebase_flag = false;
  last_steeringangle = 0;
  
  cmd_vel.linear.x = 0;
  cmd_vel.angular.z = baseAngle;

  // Show info
  RCLCPP_INFO(this->get_logger(), "[param] baseSpeed: %f", baseSpeed);
  RCLCPP_INFO(this->get_logger(), "[param] baseAngle: %f", baseAngle);
  RCLCPP_INFO(this->get_logger(), "[param] Angle_gain_p: %f", Angle_gain_p);
  RCLCPP_INFO(this->get_logger(), "[param] Angle_gain_d: %f", Angle_gain_d);
  RCLCPP_INFO(this->get_logger(), "[param] Vcmd: %f", Vcmd);
  RCLCPP_INFO(this->get_logger(), "[param] Lfw: %f", Lfw);

  // Visualization Marker Settings
  initMarker();
}

void L1Controller::initMarker()
{
  points.header.frame_id = line_strip.header.frame_id = goal_circle.header.frame_id = "odom";
  points.ns = line_strip.ns = goal_circle.ns = "Markers";
  points.action = line_strip.action = goal_circle.action = visualization_msgs::msg::Marker::ADD;
  points.pose.orientation.w = line_strip.pose.orientation.w = goal_circle.pose.orientation.w = 1.0;
  points.id = 0;
  line_strip.id = 1;
  goal_circle.id = 2;

  points.type = visualization_msgs::msg::Marker::POINTS;
  line_strip.type = visualization_msgs::msg::Marker::LINE_STRIP;
  goal_circle.type = visualization_msgs::msg::Marker::CYLINDER;

  points.scale.x = 0.2;
  points.scale.y = 0.2;
  line_strip.scale.x = 0.1;
  goal_circle.scale.x = goalRadius;
  goal_circle.scale.y = goalRadius;
  goal_circle.scale.z = 0.1;

  points.color.g = 1.0;
  points.color.a = 1.0;
  line_strip.color.b = 1.0;
  line_strip.color.a = 1.0;
  goal_circle.color.r = 1.0;
  goal_circle.color.g = 1.0;
  goal_circle.color.b = 0.0;
  goal_circle.color.a = 0.5;
}

void L1Controller::odomCB(const nav_msgs::msg::Odometry::SharedPtr odomMsg)
{
  odom = *odomMsg;
}

void L1Controller::pathCB(const nav_msgs::msg::Path::SharedPtr pathMsg)
{
  static int pathCBidx = 0;
  static nav_msgs::msg::Path last_map_path;
  
  if (pathCBidx == 0)
  {
    last_map_path.poses.clear();
  }
  
  map_path = *pathMsg;
  mapPathNum = map_path.poses.size();
  
  if (map_path.poses.size() <= 0)
  {
    for (size_t i = 0; i < last_map_path.poses.size(); i++)
    {
      map_path.poses.push_back(last_map_path.poses[i]);
    }
  }
  else
  {
    last_map_path.poses.clear();
    for (size_t i = 0; i < map_path.poses.size(); i++)
    {
      last_map_path.poses.push_back(map_path.poses[i]);
    }
  }
  pathCBidx++;
}

void L1Controller::encoderCB(const nav_msgs::msg::Odometry::SharedPtr encoderMsg)
{
  encoder = *encoderMsg;
}

void L1Controller::stopCB(const std_msgs::msg::Float64::SharedPtr stopMsg)
{
  stop_flag = stopMsg->data;
  RCLCPP_INFO(this->get_logger(), "stop_flag=%f", stop_flag);
}

void L1Controller::lineCB(const std_msgs::msg::Float64::SharedPtr lineMsg)
{
  line_wight = lineMsg->data;
}

void L1Controller::lightCB(const std_msgs::msg::String::SharedPtr msg)
{
  if (msg->data == "red")
  {
    traffic_flag = false;
  }
  else if (msg->data == "green")
  {
    traffic_flag = true;
  }
  else
  {
    traffic_flag = true;
  }
}

void L1Controller::stateCB(const std_msgs::msg::String::SharedPtr msg)
{
  if (msg->data == "movebase")
  {
    movebase_flag = true;
  }
}

void L1Controller::goalCB(const geometry_msgs::msg::PoseStamped::SharedPtr goalMsg)
{
  try
  {
    geometry_msgs::msg::PoseStamped odom_goal;
    
    // Transform goal from map frame to odom frame
    geometry_msgs::msg::TransformStamped transform = tf_buffer_->lookupTransform(
        "odom", "map", this->get_clock()->now(), 100ms);
    
    tf2::doTransform(*goalMsg, odom_goal, transform);
    
    odom_goal_pos = odom_goal.pose.position;
    goal_received = true;
    goal_reached = false;

    goal_circle.pose = odom_goal.pose;
    marker_pub->publish(goal_circle);
  }
  catch (tf2::TransformException &ex)
  {
    RCLCPP_ERROR(this->get_logger(), "%s", ex.what());
  }
}

double L1Controller::getYawFromPose(const geometry_msgs::msg::Pose &carPose)
{
  tf2::Quaternion q(
      carPose.orientation.x,
      carPose.orientation.y,
      carPose.orientation.z,
      carPose.orientation.w);
  tf2::Matrix3x3 m(q);
  double roll, pitch, yaw;
  m.getRPY(roll, pitch, yaw);
  return yaw;
}

bool L1Controller::isForwardWayPt(const geometry_msgs::msg::Point &wayPt,
                                 const geometry_msgs::msg::Pose &carPose)
{
  float car2wayPt_x = wayPt.x - carPose.position.x;
  float car2wayPt_y = wayPt.y - carPose.position.y;
  double car_theta = getYawFromPose(carPose);

  float car_car2wayPt_x = cos(car_theta) * car2wayPt_x + sin(car_theta) * car2wayPt_y;
  float car_car2wayPt_y = -sin(car_theta) * car2wayPt_x + cos(car_theta) * car2wayPt_y;

  return (car_car2wayPt_x > 0);
}

bool L1Controller::isWayPtAwayFromLfwDist(const geometry_msgs::msg::Point &wayPt, 
                                         const geometry_msgs::msg::Point &car_pos)
{
  double dx = wayPt.x - car_pos.x;
  double dy = wayPt.y - car_pos.y;
  double dist = sqrt(dx * dx + dy * dy);
  return (dist >= Lfw);
}

geometry_msgs::msg::Point L1Controller::get_odom_car2WayPtVec(const geometry_msgs::msg::Pose &carPose)
{
  geometry_msgs::msg::Point carPose_pos = carPose.position;
  double carPose_yaw = getYawFromPose(carPose);
  geometry_msgs::msg::Point forwardPt;
  geometry_msgs::msg::Point odom_car2WayPtVec;
  foundForwardPt = false;
  double car2goal_dist = getCar2GoalDist();
  bool start_flag = false;
  
  if (!goal_reached)
  {
    for (size_t i = 0; i < map_path.poses.size(); i++)
    {
      try
      {
        geometry_msgs::msg::TransformStamped transform = tf_buffer_->lookupTransform(
            "odom", "map", this->get_clock()->now(), 100ms);
        
        geometry_msgs::msg::PoseStamped odom_path_pose;
        tf2::doTransform(map_path.poses[i], odom_path_pose, transform);
        
        geometry_msgs::msg::Point odom_path_wayPt = odom_path_pose.pose.position;
        bool _isForwardWayPt = isForwardWayPt(odom_path_wayPt, carPose);

        if (_isForwardWayPt && !start_flag)
        {
          start_flag = true;
        }
        if (!start_flag)
        {
          continue;
        }

        if (_isForwardWayPt)
        {
          bool _isWayPtAwayFromLfwDist = isWayPtAwayFromLfwDist(odom_path_wayPt, carPose_pos);
          if (_isWayPtAwayFromLfwDist)
          {
            forwardPt = odom_path_wayPt;
            foundForwardPt = true;
            break;
          }
        }

        if (car2goal_dist < Lfw)
        {
          forwardPt = odom_goal_pos;
          foundForwardPt = true;
        }
      }
      catch (tf2::TransformException &ex)
      {
        RCLCPP_ERROR(this->get_logger(), "%s", ex.what());
      }
    }
  }
  else
  {
    forwardPt = odom_goal_pos;
    foundForwardPt = false;
  }

  points.points.clear();
  line_strip.points.clear();

  if (foundForwardPt && !goal_reached)
  {
    points.points.push_back(carPose_pos);
    points.points.push_back(forwardPt);
    line_strip.points.push_back(carPose_pos);
    line_strip.points.push_back(forwardPt);
  }

  marker_pub->publish(points);
  marker_pub->publish(line_strip);

  odom_car2WayPtVec.x = cos(carPose_yaw) * (forwardPt.x - carPose_pos.x) + 
                        sin(carPose_yaw) * (forwardPt.y - carPose_pos.y);
  odom_car2WayPtVec.y = -sin(carPose_yaw) * (forwardPt.x - carPose_pos.x) + 
                        cos(carPose_yaw) * (forwardPt.y - carPose_pos.y);
  return odom_car2WayPtVec;
}

double L1Controller::getEta(const geometry_msgs::msg::Pose &carPose)
{
  geometry_msgs::msg::Point odom_car2WayPtVec = get_odom_car2WayPtVec(carPose);
  return atan2(odom_car2WayPtVec.y, odom_car2WayPtVec.x);
}

double L1Controller::getCar2GoalDist()
{
  geometry_msgs::msg::Point car_pose = odom.pose.pose.position;
  double car2goal_x = odom_goal_pos.x - car_pose.x;
  double car2goal_y = odom_goal_pos.y - car_pose.y;
  return sqrt(car2goal_x * car2goal_x + car2goal_y * car2goal_y);
}

double L1Controller::getL1Distance(const double &_Vcmd)
{
  return 1.45; // Fixed L1 distance
}

double L1Controller::getSteeringAngle(double eta)
{
  return atan2((L * sin(eta)), ((Lfw / 2) + lfw * cos(eta))) * (180.0 / PI);
}

void L1Controller::goalReachingCB()
{
  if (goal_received)
  {
    double car2goal_dist = getCar2GoalDist();
    if (car2goal_dist < goalRadius)
    {
      goal_reached = true;
      goal_received = false;
      cmd_vel.linear.x = 0.0;
      
      if (all)
      {
        pub_movebase->publish(cmd_vel);
      }
      else
      {
        pub_->publish(cmd_vel);
      }
      RCLCPP_INFO(this->get_logger(), "Goal Reached !!!!!!!");
    }
  }
}

double L1Controller::isline(double line_wight)
{
  if (line_wight == 0.0)
  {
    return initbaseSpeed;
  }
  return baseSpeed + line_wight * 0.5;
}

void L1Controller::controlLoopCB()
{
  geometry_msgs::msg::Pose carPose = odom.pose.pose;
  cmd_vel.linear.x = 0;
  cmd_vel.angular.z = baseAngle;
  
  double encoder_speed = encoder.twist.twist.linear.x;
  static double speedlast;
  static double anglelast;
  
  if (movebase_flag && goal_received)
  {
    double eta = getEta(carPose);
    if (foundForwardPt)
    {
      if (!goal_reached)
      {
        if (stop_flag == 1.0 && stopIdx <= 0)
        {
          baseSpeed = slow_final * baseSpeed + 1500;
          stopIdx++;
          RCLCPP_WARN(this->get_logger(), "I GET THE FINAL GOAL AND I WILL SLOW DOWN");
        }
        if (stop_flag == 2.0 && stopIdx <= 0)
        {
          baseSpeed = fast_final * baseSpeed + 1500;
          stopIdx++;
          RCLCPP_WARN(this->get_logger(), "I GET THE FINAL GOAL AND I WILL SPEED UP");
        }
        if (stop_flag == 3.0 && stopIdx > 0)
        {
          baseSpeed = initbaseSpeed + 1500;
          RCLCPP_WARN(this->get_logger(), "I recovery the speed in case overstep the area");
        }

        cmd_vel.linear.x = baseSpeed;
        double steering_angle = getSteeringAngle(eta);
        cmd_vel.angular.z = 90 - steering_angle * Angle_gain_p - 
                           Angle_gain_d * (steering_angle - last_steeringangle);
        last_steeringangle = steering_angle;

        // Clamp values
        if (cmd_vel.linear.x < vp_min + 1500)
          cmd_vel.linear.x = vp_min + 1500;
        
        if (mapPathNum <= 0)
        {
          RCLCPP_WARN(this->get_logger(), "---------------NO PATH TO GO");
          cmd_vel.linear.x = 115;
        }
        
        if (cmd_vel.linear.x > vp_max_base + 1500)
          cmd_vel.linear.x = vp_max_base + 1500;

        if (cmd_vel.angular.z > 135)
          cmd_vel.angular.z = 135;
        else if (cmd_vel.angular.z < 45)
          cmd_vel.angular.z = 45;

        RCLCPP_INFO(this->get_logger(), "Lfw = %.2f", Lfw);
        RCLCPP_INFO(this->get_logger(), "eta = %.2f", eta * 180 / PI);
        RCLCPP_INFO(this->get_logger(), "encoder_v = %.2f", encoder_speed);
        RCLCPP_INFO(this->get_logger(), "out_speed = %.2f", cmd_vel.linear.x);
        RCLCPP_INFO(this->get_logger(), "out_angle = %.2f", cmd_vel.angular.z);
        RCLCPP_INFO(this->get_logger(), "------------------------");
      }
    }
  }
  else
  {
    cmd_vel.linear.x = 1500;
    cmd_vel.angular.z = 90;
  }
  
  speedlast = cmd_vel.linear.x;
  anglelast = cmd_vel.angular.z;
  
  if (traffic_flag)
  {
    if (all)
    {
      pub_movebase->publish(cmd_vel);
    }
    else
    {
      pub_->publish(cmd_vel);
    }
  }
  else
  {
    geometry_msgs::msg::Twist stop_cmd;
    stop_cmd.linear.x = 1500;
    stop_cmd.angular.z = 90;
    
    if (all)
    {
      pub_movebase->publish(stop_cmd);
    }
    else
    {
      pub_->publish(stop_cmd);
    }
  }
}

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<L1Controller>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}