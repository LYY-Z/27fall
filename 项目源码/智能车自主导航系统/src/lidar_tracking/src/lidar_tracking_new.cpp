#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <math.h>
#include "Control.h"

#define freq 1440
#define pi_2 1.57

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
int speed = 1900;

// 声明全局变量
static float low_pass_val = 0.0f;

void cal_point(double theta, double range, double &tmp_x, double &tmp_y)
{
     tmp_x = range * sin(theta);
     tmp_y = range * cos(theta);
}

class PubAndSub : public rclcpp::Node
{
private:
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
    geometry_msgs::msg::Twist twist;
    
public:
    PubAndSub() : Node("laser_go")
    {
        pub_ = this->create_publisher<geometry_msgs::msg::Twist>("car/cmd_vel", 5);
        sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
            "/scan", 5, std::bind(&PubAndSub::callback, this, std::placeholders::_1));
        
        // 初始化低通滤波值
        low_pass_val = 0.0;
    }
    
    void callback(const sensor_msgs::msg::LaserScan::SharedPtr laser)
    {
        char negetiveNum = 0, positiveNum = 0;
        int i = 0, j = 0, k = 0;
        double range = 0, error = 0, negetiveSum = 0, positiveSum = 0, theta = 0, tmp_x = 0, tmp_y = 0, angle = 0;
        Point_rectangular red_p[30] = {0, 0}; 
        Point_rectangular blue_p[30] = {0, 0}; 
        Point_rectangular* p = red_p;
        int flag_jk = 0;
        
        for (i = 1; i < freq; i++)
        {
            if(laser->ranges[i-1] - laser->ranges[i] >= 2.0)
            {
                theta = i * laser->angle_increment + laser->angle_min;
                cal_point(theta, laser->ranges[i], tmp_x, tmp_y);
                if((tmp_x <= 1.5 && tmp_x >= -2) && tmp_y < 2 && tmp_y > -0.1 && tmp_y != 0)  
                {
                    if(tmp_x > 0)                  
                    {
                        if(laser->ranges[i] < 2)
                        {                          
                            red_p[j].x = tmp_x;
                            red_p[j].y = tmp_y;
                            j++;
                        }
                    }
                    else
                    {
                        blue_p[k].x = tmp_x;
                        blue_p[k].y = tmp_y;
                        k++;
                    }
                }
            } 
        }

        if (j - k >= 2)
        {
            flag_jk = 1;
        }
        else if(k - j >= 2)
        {
            flag_jk = 2;
        }

        if(k >= j) 
        {
            int m = 100;
            for(int i = 1; i < k; i++)
            {
                if(sqrt(pow((blue_p[i-1].x - blue_p[i].x), 2) + pow((blue_p[i-1].y - blue_p[i].y), 2)) > 1.4)	
                {
                    m = i;	
                    break;
                }
            }
            if(m != 100)	
            {
                for(int i = j - 1; i >= 0; i--)     
                {
                    red_p[i + k - m] = red_p[i];	
                }
                for(int i = 0; i < k - m; i++) 
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
            for(int i = j - 2; i >= 0; i--)
            {
                if(sqrt(pow((red_p[i].x - red_p[i+1].x), 2) + pow((red_p[i].y - red_p[i+1].y), 2)) > 1.4)
                {
                    m = i;	
                }
            }
            if(m != 100)	
            {
                for(int i = 0; i < m + 1; i++)
                {
                    blue_p[k + i] = red_p[i];
                }		
                for(int i = 0; i < j - m - 1; i++) 
                {
                    red_p[i] = red_p[i + m + 1];
                }
                j -= (m + 1);	
                k += (m + 1);	
            }
        }

        if (j > k)   
        {
            for(i = 0; i < (j - k); i++)
                p += 1;             
            j = k;
        }
        else
        {
            k = j;
        }
        
        double gamma = 0.8;   
        for(i = k - 1; i >= 0; i--)
        {
            error = gamma * error + ((blue_p[i].x + p->x)); 
            p += 1;
        }
        
        angle = pid.PIDPositional(error * 10);
        
        switch(flag_jk)
        {
            case 1: angle += 8; break;
            case 2: angle -= 8; break;
            default: break;
        }
        
        float temp = angle; 
        
        // 使用全局变量 low_pass_val
        low_pass_val = angle;
        
        twist.angular.z = 90 + angle;
        twist.linear.x = speed;
        
        if(abs(angle) <= 10)
            twist.linear.x += 10;
        
        if(twist.angular.z > 180)
            twist.angular.z = 180;
        if(twist.angular.z < 0)
            twist.angular.z = 0;
            
        pub_->publish(twist);
    }
};

int main(int argc, char *argv[])
{
    pid.Init();
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PubAndSub>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}