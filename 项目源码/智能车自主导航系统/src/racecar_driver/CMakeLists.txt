# racecar

cmake_minimum_required(VERSION 3.5)
project(racecar_driver)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(ament_index_cpp REQUIRED)  # 添加这一行

include_directories(
  include
)

ament_export_include_directories(include)

add_library(racecar_driver SHARED src/racecar.cpp)
ament_target_dependencies(racecar_driver ament_index_cpp rclcpp sensor_msgs std_msgs)

install(TARGETS racecar_driver
  DESTINATION lib
)

install(DIRECTORY include/
  DESTINATION include/
)

ament_package()
