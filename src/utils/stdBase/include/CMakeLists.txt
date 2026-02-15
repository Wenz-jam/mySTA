cmake_minimum_required(VERSION 3.23)

add_library(stdBase INTERFACE)

# FILE_SET HEADERS Will automatically capture all header files in the current directory and make them available to users of the library.
target_sources(stdBase
    INTERFACE
        FILE_SET HEADERS
)

find_package(Boost REQUIRED CONFIG)
target_link_libraries(stdBase INTERFACE Boost::boost)
target_link_libraries(stdBase INTERFACE absl::base)