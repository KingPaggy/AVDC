cmake_minimum_required(VERSION 3.20)
project(AVDCMacGUI LANGUAGES C CXX OBJCXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_OBJCXX_STANDARD 20)
set(CMAKE_OBJCXX_STANDARD_REQUIRED ON)

if(APPLE)
  add_compile_options(-fobjc-arc)
  add_compile_options(-Wall -Wextra)
endif()

add_subdirectory(src/core)
add_subdirectory(src/ui)
add_subdirectory(src/shell)
