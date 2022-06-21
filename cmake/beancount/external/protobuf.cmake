# Populate protobuf in beancount
FetchContent_Declare(
    protobuf
    GIT_REPOSITORY https://github.com/protocolbuffers/protobuf
    GIT_TAG v21.1
    )

# populate and setup protobuf compiler
set(protobuf_INSTALL
    off
    CACHE BOOL "protobuf_INSTALL")
set(protobuf_BUILD_TESTS
    off
    CACHE BOOL "protobuf_BUILD_TESTS")
set(protobuf_BUILD_CONFORMANCE
    off
    CACHE BOOL "protobuf_BUILD_CONFORMANCE")
set(protobuf_BUILD_EXAMPLES
    off
    CACHE BOOL "protobuf_BUILD_EXAMPLES")
set(protobuf_BUILD_LIBPROTOC
    off # We don't need the runtime lib
    CACHE BOOL "protobuf_BUILD_LIBPROTOC")
set(protobuf_BUILD_SHARED_LIBS
    off # We don't need the runtime lib
    CACHE BOOL "protobuf_BUILD_SHARED_LIBS")
set(protobuf_WITH_ZLIB
    off # We don't need compression
    CACHE BOOL "protobuf_WITH_ZLIB")
set(protobuf_DISABLE_RTTI
    off # Turn on if we don't use dynamic_cast or typeid
    CACHE BOOL "protobuf_DISABLE_RTTI")
FetchContent_MakeAvailable(protobuf)

