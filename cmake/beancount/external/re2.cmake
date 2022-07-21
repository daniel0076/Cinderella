FetchContent_Declare(
    re2
    GIT_REPOSITORY https://github.com/google/re2
    GIT_TAG 2022-06-01)

if(NOT re2_POPULATED)
    FetchContent_Populate(re2)
    # neet to set cache to preserve the values until building protobuf
    set(CMAKE_CXX_STANDARD 20)
    add_subdirectory(${re2_SOURCE_DIR} ${re2_BINARY_DIR})
endif()

