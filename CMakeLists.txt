cmake_minimum_required(VERSION 3.23)

project(mySTA)

add_executable(mySTA)

target_sources(mySTA
    PRIVATE
        src/main.cc
)

target_link_libraries(mySTA 
    PRIVATE
        log
)

target_compile_features(mySTA PRIVATE cxx_std_23)

target_compile_options(mySTA PRIVATE -Wall -Wextra -Werror)

include(cmake/settings.cmake)
include(cmake/rust.cmake)

add_subdirectory(src)
add_subdirectory(include)
