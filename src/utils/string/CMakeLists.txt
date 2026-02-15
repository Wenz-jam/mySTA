cmake_minimum_required(VERSION 3.23)

add_library(str)

target_compile_features(str PRIVATE cxx_std_20)

target_sources(str
    PRIVATE
      Str.cc
      StrMap.cc
    PUBLIC
    FILE_SET HEADERS
    FILES
        Str.hh
        StrMap.hh
)

target_link_libraries(str PRIVATE absl::strings)
target_link_libraries(str PRIVATE stdBase)