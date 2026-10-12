cmake_minimum_required(VERSION 3.8)
project(lslidar_x10_msgs)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)

# 直接列出所有消息文件（相对路径）
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/LslidarX10Packet.msg"
  "msg/LslidarX10Point.msg"
  "msg/LslidarX10Scan.msg"
  "msg/LslidarX10Sweep.msg"
  "msg/LslidarX10Difop.msg"
  DEPENDENCIES builtin_interfaces std_msgs
)

ament_package()