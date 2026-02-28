cmake_minimum_required(VERSION 3.23)

if(BUILD_STATIC_LIB)
  # This is a workaround on cmake 3.22.1, should ensure static libraries are used
  # Note: There is a better approach in newer versions of CMake:
  # set(ZLIB_USE_STATIC_LIBS ON CACHE BOOL "Use static zlib" FORCE)

  set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")

  find_package(ZLIB REQUIRED)

  set(CMAKE_FIND_LIBRARY_SUFFIXES ${ORIG_CMAKE_FIND_LIBRARY_SUFFIXES})

  if(ZLIB_LIBRARIES MATCHES "\\.so(\\.|$)")
    message(FATAL_ERROR "Found dynamic zlib, but static required: ${ZLIB_LIBRARIES}")
  endif()

  message(STATUS "Linking static zlib: ${ZLIB_LIBRARIES}")
else()
  find_package(ZLIB REQUIRED)
endif()

add_library(verilog)

target_sources(verilog
    PRIVATE
        VerilogParserRustC.cc
    PUBLIC
        FILE_SET HEADERS
        FILES
            VerilogParserRustC.hh
)

target_link_libraries(verilog 
    PRIVATE
        str
        log
        dl
)

find_package(ZLIB REQUIRED)
message(STATUS "Found ZLIB: ${ZLIB_LIBRARIES} (include: ${ZLIB_INCLUDE_DIRS})")
target_link_libraries(verilog PRIVATE ZLIB::ZLIB)

set(RUST_PROJECT_NAME verilog_parser)
set(RUST_PROJECT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/verilog-rust/verilog-parser)
set(RUST_LIB_TYPE a)

target_compile_features(verilog PRIVATE cxx_std_20)

if(CMAKE_BUILD_TYPE MATCHES Debug)
    set(RUST_LIB_PATH ${RUST_PROJECT_DIR}/target/debug/lib${RUST_PROJECT_NAME}.${RUST_LIB_TYPE})
    set(RUST_BUILD_CMD_OPTION "")
else()
    set(RUST_LIB_PATH ${RUST_PROJECT_DIR}/target/release/lib${RUST_PROJECT_NAME}.${RUST_LIB_TYPE})
    set(RUST_BUILD_CMD_OPTION "--release")
endif()


message(STATUS "verilog parser rust lib path ${RUST_LIB_PATH}")

ADD_RUST_PROJ(verilog verilog_parser)