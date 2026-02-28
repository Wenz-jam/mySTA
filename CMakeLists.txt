cmake_minimum_required(VERSION 3.23)

project(mySTA)

add_executable(mySTA
        src/Visualizer.cc
        include/Visualizer.h)

target_sources(mySTA
    PRIVATE
        src/main.cc
        src/Parser/VerilogParser.cc
        src/Parser/VerilogModule.cc
        src/Parser/LibertyParser.cc
        src/Parser/CellLib.cc
        src/CircuitBuilder.cc
        src/Timer.cc
        src/Arc.cc
        src/Pin.cc
        src/Lut.cc
        src/Net.cc
)

target_link_libraries(mySTA 
    PRIVATE
        log
        verilog
        liberty
)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GRAPHVIZ REQUIRED libcgraph libcdt)
target_include_directories(mySTA PRIVATE ${GRAPHVIZ_INCLUDE_DIRS})
target_link_libraries(mySTA PRIVATE ${GRAPHVIZ_LIBRARIES})

target_compile_features(mySTA PRIVATE cxx_std_23)

target_compile_options(mySTA PRIVATE -Wall -Wextra -Werror)

include(cmake/settings.cmake)
include(cmake/rust.cmake)

add_subdirectory(src)
add_subdirectory(include)
