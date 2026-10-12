cmake_minimum_required(VERSION 3.5)
project(encoder_driver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(message_filters REQUIRED)
find_package(Eigen3 REQUIRED)

add_executable(encoder_driver_node1 src/imu_encoder_mix.cpp)
ament_target_dependencies(encoder_driver_node1
  rclcpp
  nav_msgs
  sensor_msgs
  tf2
  tf2_geometry_msgs
  message_filters
  Eigen3
)



# 旧ROS1配置保留
# ...existing code...


# ROS2 imu_encoder_mix节点（可执行文件名与ROS1保持一致）
install(TARGETS ${PROJECT_NAME}_node1
  DESTINATION lib/${PROJECT_NAME})

SET( CMAKE_CXX_FLAGS "-std=c++11 -O3")


