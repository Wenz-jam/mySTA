cmake_minimum_required(VERSION 3.23)

add_library(json INTERFACE)

# FILE_SET HEADERS Will automatically capture all header files in the current directory and make them available to users of the library.
target_sources(json
    INTERFACE
        FILE_SET HEADERS
)