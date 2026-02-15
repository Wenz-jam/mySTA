cmake_minimum_required(VERSION 3.23)

add_library(log)

target_sources(log
    PRIVATE
        Log.cc
    PUBLIC
        FILE_SET HEADERS
        FILES
            Log.hh
)

target_compile_features(log PRIVATE cxx_std_20)

find_package(glog REQUIRED CONFIG)

target_link_libraries(log PRIVATE glog::glog)