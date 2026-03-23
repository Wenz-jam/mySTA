cmake_minimum_required(VERSION 3.23)

include(shell.cmake)
include(benchmark.cmake)
if(BUILD_SHARED_LIBS)
    # 只有构建动态库时才添加 pybind11 模块
    include(pybind11.cmake)
endif()
