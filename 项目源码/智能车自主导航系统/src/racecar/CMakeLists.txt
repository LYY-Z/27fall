cmake_minimum_required(VERSION 3.5)
project(racecar)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)  # 新增 visualization_msgs 包查找

include_directories(
  src
)

ament_export_include_directories(src)


add_executable(car_controller_new_node src/car_controller_new.cpp)
ament_target_dependencies(car_controller_new_node 
  rclcpp 
  sensor_msgs 
  std_msgs
  tf2_ros
  geometry_msgs
  tf2
  nav_msgs
  tf2_geometry_msgs
  visualization_msgs  # 新增 visualization_msgs 依赖
)

install(TARGETS car_controller_new_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY src/
  DESTINATION share/${PROJECT_NAME}/src
  FILES_MATCHING PATTERN "*.hpp" PATTERN "*.h"
)

ament_package()