#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include <math.h>
#include "Control.h"
#include <string>
#include "visualization_msgs/msg/marker.hpp"
#include "std_msgs/msg/float32.hpp"

#define freq 1440  // 激光雷达扫描的频率
#define pi_2 1.57

int speed = 1500;

double rate_p[10] = { 0.8, 2.2, 0.8, 0, 0, 0, 0, 0, 0, 0 };
double max_right_dis = 1.5;  // 最大左右距离
 double max_left_dis = 1.5;

int middle_angle = 90;

int bucket_threshold = 5;
int vaild_bucket_threshold = 2;

struct Point_polar
{   
    double range;
    double theta;
};

struct Point_rectangular
{
    double x;
    double y;
};

Control::PID pid;

void cal_point(double theta, double range, double &tmp_x, double &tmp_y)
{
    tmp_x = range * sin(theta);
    tmp_y = range * cos(theta);
}

class PubAndSub : public rclcpp::Node
{
public:
    PubAndSub() : Node("laser_go")
    {
        // Declare parameters with default values
        this->declare_parameter<int>("speed", 1500);
        this->declare_parameter<double>("kp", 0.88);
        this->declare_parameter<double>("ki", 0.0);
        this->declare_parameter<double>("kd", 1.2);
        this->declare_parameter<double>("max_right_dis", 1.5);
        this->declare_parameter<double>("max_left_dis", 1.5);
        this->declare_parameter<std::string>("topic", "laser_control");
        this->declare_parameter<double>("rate1", 0.8);
        this->declare_parameter<double>("rate2", 2.2);
        this->declare_parameter<double>("rate3", 0.8);
        this->declare_parameter<int>("middle_angle", 90);
        this->declare_parameter<int>("bucket_threshold", 5);
        this->declare_parameter<int>("vaild_bucket_threshold", 2);
        this->declare_parameter<double>("speed_time", 3.0);

        // Get parameter values
        this->get_parameter("speed", speed);
        this->get_parameter("kp", pid.kp);
        this->get_parameter("ki", pid.ki);
        this->get_parameter("kd", pid.kd);
        this->get_parameter("max_right_dis", max_right_dis);
        this->get_parameter("max_left_dis", max_left_dis);
        this->get_parameter("topic", topic);
        this->get_parameter("rate1", rate_p[0]);
        this->get_parameter("rate2", rate_p[1]);
        this->get_parameter("rate3", rate_p[2]);
        this->get_parameter("middle_angle", middle_angle);
        this->get_parameter("bucket_threshold", bucket_threshold);
        this->get_parameter("vaild_bucket_threshold", vaild_bucket_threshold);
        this->get_parameter("speed_time", speed_time);

        pub_ = this->create_publisher<geometry_msgs::msg::Twist>(topic, 5);
        sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>("/scan", 5, std::bind(&PubAndSub::callback, this, std::placeholders::_1));
        marker_pub = this->create_publisher<visualization_msgs::msg::Marker>("visualization_marker", 5);
        err_pub_ = this->create_publisher<std_msgs::msg::Float32>("/error", 10);
        start_time = this->now();
    }
    void callback(const sensor_msgs::msg::LaserScan::SharedPtr laser);
private:
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
    rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr marker_pub;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr err_pub_;
    geometry_msgs::msg::Twist twist;
    std::string topic;
    rclcpp::Time start_time;
    double speed_time;
};

void PubAndSub::callback(const sensor_msgs::msg::LaserScan::SharedPtr laser)
{
    int i = 0, j = 0, k = 0, flag_jk = 0;
    double range = 0, error = 0, theta = 0, tmp_x = 0, tmp_y = 0, angle = 0, rate_sum = 0, error_sum = 0;
    Point_rectangular red_p[30] = {};
    Point_rectangular blue_p[30] = {};

    for (i = 1; i < freq - bucket_threshold; i++)
    {
        if (laser->ranges[i - 1] - laser->ranges[i] >= 2.0 && laser->ranges[i] < 2.0 && laser->ranges[i] != 0 && laser->ranges[i] > 0.25 && laser->ranges[i - 1] - laser->ranges[i+1] >= 2.0)
        {
            int continue_ranges = 0;
            int continue_dectect = 0;
            for (int idx = 1; idx < bucket_threshold; idx++)   
            {
                if (std::abs(laser->ranges[i] - laser->ranges[i+idx]) < 0.2)
                {
                    continue_ranges++;
                    if (continue_ranges >= vaild_bucket_threshold)    
                    {
                        continue_dectect = 1;
                        break;
                    }
                }
            }
            if (continue_dectect == 1)
            {
                theta = i * laser->angle_increment + laser->angle_min;
                cal_point(theta, laser->ranges[i], tmp_x, tmp_y);
                if ((tmp_x <= max_left_dis && tmp_x >= -max_right_dis) && tmp_y < 2 && tmp_y > -0.2 && tmp_y != 0 )  
                {
                    if (tmp_x > 0)                  
                    {
                        if (laser->ranges[i] < 2)
                        {                          
                            red_p[j].x = tmp_x;
                            red_p[j].y = tmp_y;
                            RCLCPP_INFO(this->get_logger(), "_____found red bucket point:(%.2f,%.2f)", red_p[j].x, red_p[j].y);
                            j++;
                        }
                    }
                    else
                    {
                        blue_p[k].x = tmp_x;
                        blue_p[k].y = tmp_y;
                        RCLCPP_INFO(this->get_logger(), "______found blue bucket point:(%.2f,%.2f)", blue_p[k].x, blue_p[k].y);
                        k++;
                    }
                }
            }
        }
    }
    RCLCPP_INFO(this->get_logger(), "j=%d,k=%d", j, k);

    if (k >= j) 
    {
        int m = 100;
        for (int i = 1; i < k; i++)
        {
            if (sqrt(pow((blue_p[i-1].x-blue_p[i].x),2)+pow((blue_p[i-1].y-blue_p[i].y),2)) > 1.4)    
            {
                m = i;    
                break;
            }
        }
        if (m != 100)    
        {
            for (int i = j - 1; i >= 0; i--)     
            {
                red_p[i + k - m] = red_p[i];    
            }
            for (int i = 0; i < k - m; i++) 
            {
                red_p[i] = blue_p[m + i];
            }
            j += (k - m);
            k = m;
        }
    }   
    else
    {
        int m = 100;
        for (int i = j-2; i >= 0; i--)
        {
            if (sqrt(pow((red_p[i].x-red_p[i+1].x),2)+pow((red_p[i].y-red_p[i+1].y),2)) > 1.4)
            {
                m = i;    
            }
        }
        if (m != 100)    
        {
            for (int i = 0; i <  m + 1;  i++)
            {
                blue_p[k + i] = red_p[i];
            }       
            for (int i = 0; i < j - m - 1;  i++) 
            {
                red_p[i] = red_p[i + m + 1];
            }
            j -= (m+1);
            k += (m + 1);
        }
    }

    if(j > 3)
    {
        for (int i = 0; i < 3; i++)
        {
            red_p[i] = red_p[i+1];
        }
        j = 3;
    }
    if(k > 3)
    {
        k = 3;
    }
    if(j > k && k != 0)
    {
        if(k == 1)
        {
            if(j > 2)
            {
                for (int i = 0; i < 2; i++)
                {
                    red_p[i] = red_p[i+1];
                    j = 2;
                }
            }
            blue_p[1] = blue_p[0];
            k = 2;
        }
        else if(k == 2)
        {
            blue_p[2] = blue_p[1];
            k = 3;
        }
    }
    else if(k > j && j != 0)
    {
        if(j == 1)
        {
            k = 2;
            red_p[1] = red_p[0];
            j = 2;
        }
        else if(j == 2)
        {
            red_p[2] = red_p[1];
            red_p[1] = red_p[0];
            j = 3;
        }
    }

    Point_rectangular* point_to_red = &red_p[j-1];
    int error_count = j < k ? j : k;
    double min_left = 0, min_right = 0;
    if (error_count)
    {
        for (int i = 0; i < error_count; i++)   
        {
            error_sum += (blue_p[i].x + point_to_red->x) * rate_p[i];
            rate_sum += rate_p[i];
            point_to_red--;
        }
        error = error_sum / rate_sum * 53.33;
    }
    std_msgs::msg::Float32 msg_error;
    msg_error.data = error;
    err_pub_->publish(msg_error);

    angle  = pid.PIDPositional(error);
    min_left = sqrt(red_p[3].x * red_p[3].x + red_p[3].y * red_p[3].y);
    min_right = sqrt(blue_p[1].x * blue_p[1].x + blue_p[1].y * blue_p[1].y);
    twist.linear.x = speed;
    twist.angular.z = middle_angle + angle;
    if (std::abs(angle) >= 20)
    {
        twist.linear.x -= 10;
    }
    if (twist.angular.z > 180)
        twist.angular.z = 180;
    if (twist.angular.z < 0)
        twist.angular.z = 0;
    pub_->publish(twist);
    RCLCPP_INFO(this->get_logger(), "angle:%.2f, speed:%.2f ,error:%.2f", twist.angular.z, twist.linear.x, error);

    visualization_msgs::msg::Marker red_markers, blue_markers;
    red_markers.header.frame_id = "laser_link";
    red_markers.header.stamp = this->now();
    blue_markers.header.frame_id = "laser_link";
    blue_markers.header.stamp = this->now();

    red_markers.ns = "red_buckets";
    red_markers.id = 0;
    blue_markers.ns = "blue_buckets";
    blue_markers.id = 0;

    red_markers.type = visualization_msgs::msg::Marker::POINTS;
    red_markers.action = visualization_msgs::msg::Marker::ADD;
    blue_markers.type = visualization_msgs::msg::Marker::POINTS;
    blue_markers.action = visualization_msgs::msg::Marker::ADD;

    red_markers.pose.orientation.w = 1.0;
    blue_markers.pose.orientation.w = 1.0;

    red_markers.scale.x = 0.2;
    red_markers.scale.y = 0.2;
    blue_markers.scale.x = 0.2;
    blue_markers.scale.y = 0.2;

    red_markers.color.r = 1.0f;
    red_markers.color.g = 0.0f;
    red_markers.color.b = 0.0f;
    red_markers.color.a = 1.0;
    blue_markers.color.r = 0.0f;
    blue_markers.color.g = 0.0f;
    blue_markers.color.b = 1.0f;
    blue_markers.color.a = 1.0;

    red_markers.points.clear();
    blue_markers.points.clear();

    for (int i = 0; i < j; ++i) {
        geometry_msgs::msg::Point p;
        p.x = red_p[i].y;
        p.y = red_p[i].x;
        p.z = 0;
        red_markers.points.push_back(p);
    }
    for (int i = 0; i < k; ++i) {
        geometry_msgs::msg::Point p;
        p.x = blue_p[i].y;
        p.y = blue_p[i].x;
        p.z = 0;
        blue_markers.points.push_back(p);
    }

    marker_pub->publish(red_markers);
    marker_pub->publish(blue_markers);
}

int main(int argc, char *argv[])
{
    pid.Init();
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PubAndSub>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
