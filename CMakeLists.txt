cmake_minimum_required(VERSION 3.23)

project(mySTA)

add_library(mySTAcore)

target_sources(mySTAcore
    PRIVATE
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

target_link_libraries(mySTAcore
    PUBLIC
        log
        verilog
        liberty
)

target_compile_features(mySTAcore PRIVATE cxx_std_23)

target_compile_options(mySTAcore PRIVATE -Wall -Wextra -Werror)

include(cmake/settings.cmake)
include(cmake/rust.cmake)

add_subdirectory(src)
add_subdirectory(include)
