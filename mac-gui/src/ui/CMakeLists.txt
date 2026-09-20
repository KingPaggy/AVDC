add_library(ui STATIC
  UIManager.mm
  Palette.mm
  ${CMAKE_SOURCE_DIR}/third_party/imgui/imgui.cpp
  ${CMAKE_SOURCE_DIR}/third_party/imgui/imgui_demo.cpp
  ${CMAKE_SOURCE_DIR}/third_party/imgui/imgui_draw.cpp
  ${CMAKE_SOURCE_DIR}/third_party/imgui/imgui_tables.cpp
  ${CMAKE_SOURCE_DIR}/third_party/imgui/imgui_widgets.cpp
  ${CMAKE_SOURCE_DIR}/third_party/imgui/backends/imgui_impl_metal.mm
  ${CMAKE_SOURCE_DIR}/third_party/imgui/backends/imgui_impl_osx.mm
)

target_include_directories(ui PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/..)

target_include_directories(ui PRIVATE
  ${CMAKE_SOURCE_DIR}/third_party/imgui
  ${CMAKE_SOURCE_DIR}/third_party/imgui/backends
)

target_link_libraries(ui PUBLIC core)
