cmake_minimum_required(VERSION 3.5)
project(lslidar_x10)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(lslidar_x10_msgs REQUIRED)

include_directories(
  include
)

ament_export_include_directories(include)

add_executable(lslidar_x10_node src/lslidar_x10_driver_node.cc src/lslidar_x10_driver.cc src/input.cc src/lsiosr.cpp)
ament_target_dependencies(lslidar_x10_node rclcpp sensor_msgs std_msgs geometry_msgs lslidar_x10_msgs)

install(TARGETS lslidar_x10_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include/
)

ament_package()
