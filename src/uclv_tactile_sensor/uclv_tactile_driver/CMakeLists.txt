cmake_minimum_required(VERSION 3.8)
project(uclv_tactile_driver)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

# Migrating codes
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(uclv_tactile_interfaces REQUIRED)
find_package(serial REQUIRED)

include_directories(
  include
)

add_executable(read_tactile_serial src/read_tactile_serial_node.cpp)
ament_target_dependencies(read_tactile_serial rclcpp uclv_tactile_interfaces serial)

add_executable(remove_bias src/remove_bias_node.cpp)
ament_target_dependencies(remove_bias rclcpp rclcpp_action uclv_tactile_interfaces)

install(TARGETS
  read_tactile_serial
  remove_bias
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()


ament_package()