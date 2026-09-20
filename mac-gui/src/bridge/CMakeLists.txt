add_library(bridge STATIC
  AVDCBridge.mm
)

target_include_directories(bridge PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/..)

if(APPLE)
  target_link_libraries(bridge PRIVATE "-framework Foundation")
endif()

# ---- Bridge 冒烟测试（mock CLI，离线） ----
add_executable(bridge_test
  test/test_bridge.mm
)

target_compile_definitions(bridge_test PRIVATE
  SRC_DIR="${CMAKE_CURRENT_SOURCE_DIR}"
)

target_include_directories(bridge_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)

target_link_libraries(bridge_test PRIVATE bridge)
