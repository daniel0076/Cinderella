include(ExternalProject)
ExternalProject_Add(
    mpdecimal
    URL https://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.5.1.tar.gz
    URL_HASH SHA256=9f9cd4c041f99b5c49ffb7b59d9f12d95b683d88585608aa56a6307667b2b21f
    CONFIGURE_COMMAND ./configure --prefix=${CMAKE_CURRENT_BINARY_DIR}/external
    BUILD_COMMAND make
    BUILD_IN_SOURCE TRUE
    BUILD_BYPRODUCTS ${CMAKE_CURRENT_BINARY_DIR}/external/lib/libmpdec++.a ${CMAKE_CURRENT_BINARY_DIR}/external/lib/libmpdec.a
    )

add_library(libmpdec STATIC IMPORTED)
set_target_properties(libmpdec PROPERTIES
    IMPORTED_LOCATION ${CMAKE_CURRENT_BINARY_DIR}/external/lib/libmpdec.a
    INTERFACE_INCLUDE_DIRECTORIES ${CMAKE_CURRENT_BINARY_DIR}/external/include
    )
add_library(libmpdec++ STATIC IMPORTED)
set_target_properties(libmpdec++ PROPERTIES
    IMPORTED_LOCATION ${CMAKE_CURRENT_BINARY_DIR}/external/lib/libmpdec++.a
    INTERFACE_INCLUDE_DIRECTORIES ${CMAKE_CURRENT_BINARY_DIR}/external/include
    )


#set(MPDECIMAL_INC ${mpdecimal_BINARY_DIR}/include)
#set(MPDECIMAL_LIB ${mpdecimal_BINARY_DIR}/lib)
#list(APPEND MPDECIMAL_HDR ${MPDECIMAL_INC}/decimal.hh ${MPDECIMAL_INC}/mpdecimal.h)
#list(APPEND MPDECIMAL_SO ${MPDECIMAL_LIB}/libmpdec.dylib ${MPDECIMAL_LIB}/libmpdec++.dylib)
#
#add_custom_command(
#    OUTPUT ${MPDECIMAL_HDR} ${MPDECIMAL_SO}
#    WORKING_DIRECTORY ${mpdecimal_SOURCE_DIR}
#    DEPENDS mpdecimal
#    COMMAND ${mpdecimal_SOURCE_DIR}/configure --prefix=${mpdecimal_BINARY_DIR} && make install)
#
