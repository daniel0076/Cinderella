FetchContent_Declare(
    mpdecimal
    URL https://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.5.1.tar.gz
    URL_HASH SHA256=9f9cd4c041f99b5c49ffb7b59d9f12d95b683d88585608aa56a6307667b2b21f
)
FetchContent_MakeAvailable(mpdecimal)

set(MPDECIMAL_INC ${mpdecimal_BINARY_DIR}/include)
set(MPDECIMAL_LIB ${mpdecimal_BINARY_DIR}/lib)
list(APPEND MPDECIMAL_HDR ${MPDECIMAL_INC}/decimal.hh ${MPDECIMAL_INC}/mpdecimal.h)
list(APPEND MPDECIMAL_AR ${MPDECIMAL_LIB}/libmpdec.a ${MPDECIMAL_LIB}/libmpdec++.a)

add_custom_command(
    OUTPUT ${MPDECIMAL_HDR} ${MPDECIMAL_AR}
    WORKING_DIRECTORY ${mpdecimal_SOURCE_DIR}
    COMMAND ${mpdecimal_SOURCE_DIR}/configure --prefix=${mpdecimal_BINARY_DIR} && make install
)

