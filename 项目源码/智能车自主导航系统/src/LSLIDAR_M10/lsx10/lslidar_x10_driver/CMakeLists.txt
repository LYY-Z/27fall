cmake_minimum_required(VERSION 3.5)
project(lslidar_x10_driver)

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

add_library(lslidar_x10_driver SHARED src/lslidar_x10_driver.cpp src/input.cpp src/lsiosr.cpp)
ament_target_dependencies(lslidar_x10_driver rclcpp sensor_msgs std_msgs geometry_msgs lslidar_x10_msgs)

add_executable(lslidar_x10_driver_node src/lslidar_x10_driver_node.cpp)
target_link_libraries(lslidar_x10_driver_node lslidar_x10_driver)
ament_target_dependencies(lslidar_x10_driver_node rclcpp sensor_msgs std_msgs geometry_msgs lslidar_x10_msgs)

install(TARGETS lslidar_x10_driver lslidar_x10_driver_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include/
)

ament_package()

