set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(pySTA pybind11.cc)
target_link_libraries(pySTA PRIVATE mySTAcore)
install(TARGETS pySTA LIBRARY DESTINATION /home/wenz/git/mySTA/.venv/lib/python3.13/site-packages/)

pybind11_add_module(pyVerilogParser PyVerilogParser.cc)
target_link_libraries(pyVerilogParser PRIVATE mySTAcore)
install(TARGETS pyVerilogParser LIBRARY DESTINATION /home/wenz/git/mySTA/.venv/lib/python3.13/site-packages/)

pybind11_add_module(pyLibertyParser PyLibertyParser.cc)
target_link_libraries(pyLibertyParser PRIVATE mySTAcore)
install(TARGETS pyLibertyParser LIBRARY DESTINATION /home/wenz/git/mySTA/.venv/lib/python3.13/site-packages/)

add_custom_target(install_py
        DEPENDS pySTA pyVerilogParser pyLibertyParser
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:pySTA>
        "${CMAKE_SOURCE_DIR}/.venv/lib/python3.13/site-packages/"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:pyVerilogParser>
        "${CMAKE_SOURCE_DIR}/.venv/lib/python3.13/site-packages/"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:pyLibertyParser>
        "${CMAKE_SOURCE_DIR}/.venv/lib/python3.13/site-packages/"
        COMMENT "Copying pybind11 modules to virtual environment"
)