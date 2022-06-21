project(cinderella)

add_executable(${PROJECT_NAME} ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/main.cpp)

set_target_properties(${PROJECT_NAME} PROPERTIES CXX_STANDARD 20)

target_link_libraries(${PROJECT_NAME} beancount)
