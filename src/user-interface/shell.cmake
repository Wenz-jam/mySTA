add_executable(mySTAshell)

target_sources(mySTAshell
    PRIVATE
        shell.cc
        shell/Context.cc
        shell/Commands.cc
        shell/ReportTiming.cc
)

target_link_libraries(mySTAshell
    PRIVATE
        mySTAcore
        nlohmann_json
)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GRAPHVIZ REQUIRED libcgraph libcdt)
target_include_directories(mySTAshell PRIVATE ${GRAPHVIZ_INCLUDE_DIRS})
target_link_libraries(mySTAshell PRIVATE ${GRAPHVIZ_LIBRARIES})

pkg_check_modules(READLINE REQUIRED readline)
target_link_libraries(mySTAshell PRIVATE ${READLINE_LIBRARIES})
target_include_directories(mySTAshell PRIVATE ${READLINE_INCLUDE_DIRS})
target_compile_options(mySTAshell PRIVATE ${READLINE_CFLAGS_OTHER})

add_custom_target(run
        COMMAND $<TARGET_FILE:mySTAshell>
        DEPENDS mySTAshell
        COMMENT "Running mySTAshell..."
        WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
)
