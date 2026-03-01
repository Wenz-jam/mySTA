set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(pySTA pybind11.cc)
target_link_libraries(pySTA PRIVATE mySTAcore)
install(TARGETS pySTA DESTINATION CMAKE_BINARY_DIR)