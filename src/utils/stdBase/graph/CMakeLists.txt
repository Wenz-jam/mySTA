cmake_minimum_required(VERSION 3.23)

add_library(graph)

target_compile_features(graph PRIVATE cxx_std_17)

target_sources(graph
    PRIVATE
      AdjListGraphV.cc
    PUBLIC
    FILE_SET HEADERS
    FILES
        AdjListGraphV.hh
)

target_link_libraries(graph PRIVATE absl::btree)
target_link_libraries(graph PRIVATE stdBase)