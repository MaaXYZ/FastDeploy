# Try modern CMake Config mode first (macOS Homebrew, Linux apt, vcpkg)
find_package(Eigen3 ${Eigen3_FIND_VERSION} CONFIG QUIET)
if(TARGET Eigen3::Eigen OR Eigen3_FOUND)
  set(Eigen3_FOUND TRUE)
  set(EIGEN3_FOUND TRUE)
  return()
endif()

# Fallback: Find in-tree third_party/eigen or prefix path
find_path(EIGEN3_INCLUDE_DIR NAMES signature_of_eigen3_matrix_library
  HINTS
  ENV EIGEN3_ROOT
  ENV EIGEN3_ROOT_DIR
  "${CMAKE_CURRENT_SOURCE_DIR}/third_party/eigen"
  PATHS
  ${CMAKE_PREFIX_PATH}
  ${CMAKE_INSTALL_PREFIX}/include
  PATH_SUFFIXES eigen3 eigen
)

if(EIGEN3_INCLUDE_DIR)
  set(EIGEN3_FOUND TRUE)
  set(Eigen3_FOUND TRUE)
  if(NOT TARGET Eigen3::Eigen)
    add_library(Eigen3::Eigen INTERFACE IMPORTED)
    set_target_properties(Eigen3::Eigen PROPERTIES
      INTERFACE_INCLUDE_DIRECTORIES "${EIGEN3_INCLUDE_DIR}")
  endif()
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Eigen3 DEFAULT_MSG EIGEN3_INCLUDE_DIR)

