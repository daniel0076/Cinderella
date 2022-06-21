FetchContent_Declare(
    absl
    GIT_REPOSITORY https://github.com/abseil/abseil-cpp
    GIT_TAG d2c5297a3c3948de765100cb7e5cccca1210d23c)

if(NOT absl_POPULATED)
    FetchContent_Populate(absl)
    # neet to set cache to preserve the values until building protobuf
    set(CMAKE_CXX_STANDARD 20)
    add_subdirectory(${absl_SOURCE_DIR} ${absl_BINARY_DIR})
endif()

