add_executable(mySTABenchmark)

target_sources(mySTABenchmark
    PRIVATE
        benchmark.cc
)

target_link_libraries(mySTABenchmark
    PRIVATE
        mySTAcore
        profiler
)