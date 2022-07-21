project(beancount)

include(${CMAKE_CURRENT_LIST_DIR}/external/protobuf.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/external/mpdecimal.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/external/absl.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/external/re2.cmake)

FetchContent_Declare(
    beancount
    GIT_REPOSITORY https://github.com/beancount/beancount
    GIT_TAG de75204ecfc08226413745d50bca935a04d8a9fe)
FetchContent_MakeAvailable(beancount)

file(GLOB PROTO_FILES
    LIST_DIRECTORIES false CONFIGURE_DEPENDS
    "${beancount_SOURCE_DIR}/beancount/ccore/*.proto"
    "${beancount_SOURCE_DIR}/beancount/cparser/*.proto")

set(PROTOC ${protobuf_BINARY_DIR}/protoc)
foreach(PROTO_FILE ${PROTO_FILES})
    get_filename_component(FILENAME ${PROTO_FILE} NAME_WE)
    get_filename_component(FILE_DIR ${PROTO_FILE} DIRECTORY)
    get_filename_component(FILE_ABS ${PROTO_FILE} ABSOLUTE)

    set(HDR "${FILE_DIR}/${FILENAME}.pb.h")
    set(SRC "${FILE_DIR}/${FILENAME}.pb.cc")
    list(APPEND PROTO_GENERATED_HDR ${HDR})
    list(APPEND PROTO_GENERATED_SRC ${SRC})

    add_custom_command(
        OUTPUT ${HDR} ${SRC}
        COMMAND ${PROTOC} -I=${beancount_SOURCE_DIR} --cpp_out=${beancount_SOURCE_DIR} ${FILE_ABS}
        DEPENDS ${FILE_ABS} ${PROTOC})

endforeach()

add_library(${PROJECT_NAME} STATIC
    ${PROTO_GENERATED_SRC}
    ${beancount_SOURCE_DIR}/beancount/cparser/ledger.cc
    ${beancount_SOURCE_DIR}/beancount/ccore/precision.cc
    ${beancount_SOURCE_DIR}/beancount/ccore/currency.cc
    ${beancount_SOURCE_DIR}/beancount/ccore/inventory.cc
    ${beancount_SOURCE_DIR}/beancount/ccore/std_utils.cc
    ${beancount_SOURCE_DIR}/beancount/ccore/number.cc
    ${beancount_SOURCE_DIR}/beancount/utils/errors.cc
)

set_target_properties(${PROJECT_NAME} PROPERTIES CXX_STANDARD 20)
#add_dependencies(${PROJECT_NAME} mpdecimal)

target_link_libraries(${PROJECT_NAME} PRIVATE
    absl::status
    absl::hash
    re2::re2
    protobuf::libprotobuf
    ${MPDECIMAL_AR}
)

target_include_directories(${PROJECT_NAME} PUBLIC
    ${protobuf_SOURCE_DIR}/src
    ${beancount_SOURCE_DIR}
    ${beancount_SOURCE_DIR}/beancount/utils
    ${absl_SOURCE_DIR}
    ${MPDECIMAL_INC}
    ${re2_SOURCE_DIR}
)
