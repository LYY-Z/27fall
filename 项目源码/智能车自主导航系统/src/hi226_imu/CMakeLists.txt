cmake_minimum_required(VERSION 3.5)
project(hi226_imu)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

include_directories(
  include
)

add_executable(hi226_imu_node src/Imu.cpp src/imu_data_decode.c src/packet.c)
ament_target_dependencies(hi226_imu_node rclcpp sensor_msgs std_msgs geometry_msgs)
install(TARGETS hi226_imu_node
  DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY include/
  DESTINATION include/)
