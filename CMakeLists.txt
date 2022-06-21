cmake_minimum_required(VERSION 3.22)

project(cinderella VERSION 2.0.0 LANGUAGES C CXX)

include(FetchContent)
include(cmake/beancount/beancount.cmake)
add_subdirectory(cinderella)
