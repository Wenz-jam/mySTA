cmake_minimum_required(VERSION 3.23)

add_library(sta-solver INTERFACE)

target_compile_features(sta-solver INTERFACE cxx_std_23)

# Let CMake automatically capture all header files in the current directory
target_sources(sta-solver
    INTERFACE
        FILE_SET HEADERS
)