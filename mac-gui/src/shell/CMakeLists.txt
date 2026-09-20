# ---- SwiftUI 视图：swiftc 编译为对象 + ObjC 桥接头 ----
# 多文件时 swiftc 不支持 -o 单目标，改为在 build 目录输出
# 每源文件同名 .o（WORKING_DIRECTORY = build 目录）
set(SWIFT_MODULE AVDCMacGUIModule)
set(SWIFT_HEADER ${CMAKE_CURRENT_BINARY_DIR}/AVDCMacGUI-Swift.h)
set(SWIFT_OBJ ${CMAKE_CURRENT_BINARY_DIR}/Sidebar.o)
set(SWIFT_OBJ2 ${CMAKE_CURRENT_BINARY_DIR}/InfoBar.o)

add_custom_command(
  OUTPUT ${SWIFT_OBJ} ${SWIFT_OBJ2} ${SWIFT_HEADER}
  COMMAND swiftc -emit-object -parse-as-library
          -module-name ${SWIFT_MODULE}
          -emit-objc-header-path ${SWIFT_HEADER}
          ${CMAKE_CURRENT_SOURCE_DIR}/Sidebar.swift
          ${CMAKE_CURRENT_SOURCE_DIR}/InfoBar.swift
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  DEPENDS Sidebar.swift InfoBar.swift
  COMMENT "Compiling SwiftUI views (Sidebar + InfoBar)"
)

set_source_files_properties(${SWIFT_OBJ} ${SWIFT_OBJ2} ${SWIFT_HEADER}
  PROPERTIES GENERATED TRUE)

add_executable(app
  main.mm
  AppDelegate.h
  AppDelegate.mm
  Menus.h
  Menus.mm
  ${SWIFT_OBJ}
  ${SWIFT_OBJ2}
)

target_include_directories(app PRIVATE ${CMAKE_CURRENT_BINARY_DIR})

target_link_libraries(app PRIVATE ui core)

if(APPLE)
  target_link_libraries(app PRIVATE
    "-framework Cocoa"
    "-framework AppKit"
    "-framework Metal"
    "-framework MetalKit"
    "-framework QuartzCore"
    "-framework GameController"
    "-framework SwiftUI"
    "-framework Combine"
  )
  # Swift 标准库：SDK 内编译期库 + 系统运行时
  execute_process(
    COMMAND xcrun --show-sdk-path
    OUTPUT_VARIABLE SWIFT_SDK
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  target_link_libraries(app PRIVATE
    "-L${SWIFT_SDK}/usr/lib/swift"
    "-Wl,-rpath,/usr/lib/swift"
  )
endif()
