cmake_minimum_required(VERSION 3.23)

add_library(liberty)

target_sources(liberty
    PRIVATE
        Lib.cc
        LibClassifyCell.cc
        LibParserRustC.cc
    PUBLIC
    FILE_SET HEADERS
    FILES
        Config.hh
        Type.hh
        Lib.hh
        LibClassifyCell.hh
        LibParserRustC.hh
)

target_include_directories(liberty
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(liberty
    PUBLIC
        stdBase
        str
        sta-solver
        log
        dl
        nlohmann_json
)

target_compile_features(verilog PRIVATE cxx_std_20)

set(RUST_PROJECT_NAME liberty_parser)
set(RUST_PROJECT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/lib-rust/liberty-parser)
set(RUST_LIB_TYPE a)

set(CMAKE_BUILD_TYPE "Release")

if(CMAKE_BUILD_TYPE MATCHES Debug)
    set(RUST_LIB_PATH ${RUST_PROJECT_DIR}/target/debug/lib${RUST_PROJECT_NAME}.${RUST_LIB_TYPE})
    set(RUST_BUILD_CMD_OPTION "")
else()
    set(RUST_LIB_PATH ${RUST_PROJECT_DIR}/target/release/lib${RUST_PROJECT_NAME}.${RUST_LIB_TYPE})
    set(RUST_BUILD_CMD_OPTION "--release")
endif()

set(CMAKE_BUILD_TYPE "Debug")

message(STATUS "liberty parser rust lib path ${RUST_LIB_PATH}")

ADD_RUST_PROJ(liberty liberty_parser)