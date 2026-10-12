cmake_minimum_required(VERSION 3.5)
project(serial)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)

include_directories(
  include
)

ament_export_include_directories(include)

add_library(serial SHARED src/serial.cc src/impl/unix.cc src/impl/win.cc src/impl/list_ports/list_ports_linux.cc src/impl/list_ports/list_ports_osx.cc src/impl/list_ports/list_ports_win.cc)

install(TARGETS serial
  DESTINATION lib
)

install(DIRECTORY include/
  DESTINATION include/
)

ament_package()
