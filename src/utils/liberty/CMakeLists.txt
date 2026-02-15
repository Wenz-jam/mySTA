cmake_minimum_required(VERSION 3.23)

set (CMAKE_CXX_STANDARD 20)
set (CMAKE_BUILD_TYPE "Release")

set(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -DNDEBUG")

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
    PRIVATE
        stdBase
        str
        sta-solver
        log
        dl
        nlohmann_json
)

set(RUST_PROJECT_NAME liberty_parser)
set(RUST_PROJECT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/lib-rust/liberty-parser)
set(RUST_LIB_TYPE a)

if(CMAKE_BUILD_TYPE MATCHES Debug)
    set(RUST_LIB_PATH ${RUST_PROJECT_DIR}/target/debug/lib${RUST_PROJECT_NAME}.${RUST_LIB_TYPE})
    set(RUST_BUILD_CMD_OPTION "")
else()
    set(RUST_LIB_PATH ${RUST_PROJECT_DIR}/target/release/lib${RUST_PROJECT_NAME}.${RUST_LIB_TYPE})
    set(RUST_BUILD_CMD_OPTION "--release")
endif()

message(STATUS "liberty parser rust lib path ${RUST_LIB_PATH}")

ADD_RUST_PROJ(liberty liberty_parser)