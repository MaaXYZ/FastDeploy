cmake_minimum_required(VERSION 3.20)
project(fastdeploy_ppocr CXX)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

find_package(OpenCV COMPONENTS core imgproc)
find_package(onnxruntime REQUIRED)
find_package(Eigen3 REQUIRED)
message("OpenCV_LIBS: ${OpenCV_LIBS} ${OPENCV_core_FOUND} ${OPENCV_WORLD_FOUND}")

# ONNX Runtime flattens the headers of every enabled execution provider into
# <onnxruntime/>, so <onnxruntime/webgpu_provider_factory.h> exists exactly when
# that ONNX Runtime was built with the WebGPU EP (the same signal the Maa
# side uses for DirectML/CoreML). FastDeploy always compiles the WebGPU device
# path and falls back to Device::CPU at runtime when the EP is unavailable, so
# this reports what the linked ONNX Runtime can actually do -- pick the ONNX
# Runtime accordingly if you need the device.
if(EXISTS "${onnxruntime_INCLUDE_DIR}/webgpu_provider_factory.h")
    set(WITH_WEBGPU ON)
else()
    set(WITH_WEBGPU OFF)
endif()
message(STATUS "WITH_WEBGPU: ${WITH_WEBGPU} (onnxruntime_INCLUDE_DIR=${onnxruntime_INCLUDE_DIR})")

option(WITH_CUDA "Whether WITH_CUDA=ON, will enable onnxruntime-gpu/paddle-inference-gpu" OFF)
option(PRINT_INFO "Print more debug info while running" OFF)

if(WITH_CUDA)
    add_definitions (-Wno-format-security)
    enable_language(CUDA)
    include(cmake/cuda.cmake)
    message(STATUS "CUDA compiler: ${CMAKE_CUDA_COMPILER}, version: ${CMAKE_CUDA_COMPILER_ID} ${CMAKE_CUDA_COMPILER_VERSION}")
    add_definitions(-DWITH_CUDA)
    add_definitions(-DENABLE_CUDA_PREPROCESS)
    find_library(CUDA_LIB cudart ${CUDA_DIRECTORY}/lib64)
    include_directories(PRIVATE ${CUDA_DIRECTORY}/include)
endif()

if(PRINT_INFO)
    add_definitions(-DPRINT_INFO)
endif()

file(GLOB CORE_SRC fastdeploy/*.cc fastdeploy/core/*.cc fastdeploy/runtime/*.cc fastdeploy/utils/*.cc)
list(FILTER CORE_SRC EXCLUDE REGEX ".*pybind.*")
add_library(FastDeploy_Core OBJECT ${CORE_SRC})

target_compile_definitions(FastDeploy_Core PRIVATE ENABLE_ORT_BACKEND)
target_include_directories(FastDeploy_Core PUBLIC 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>  # for build
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDE}>  # for install
)
target_link_libraries(FastDeploy_Core PRIVATE onnxruntime::onnxruntime)

file(GLOB_RECURSE BACKEND_ONNXRUNTIME_SRC fastdeploy/runtime/backends/ort/*.cc)
list(FILTER BACKEND_ONNXRUNTIME_SRC EXCLUDE REGEX ".*pybind.*")
if(WITH_CUDA)
    list(APPEND BACKEND_ONNXRUNTIME_SRC
        fastdeploy/runtime/backends/common/cuda/adaptive_pool2d_kernel.cu
    )
endif()
add_library(FastDeploy_Backend_ONNXRuntime OBJECT ${BACKEND_ONNXRUNTIME_SRC})
target_include_directories(FastDeploy_Backend_ONNXRuntime PUBLIC ${onnxruntime_INCLUDE_DIRS}) 
target_link_libraries(FastDeploy_Backend_ONNXRuntime PRIVATE FastDeploy_Core onnxruntime::onnxruntime)
if(WITH_CUDA)
    target_link_libraries(FastDeploy_Backend_ONNXRuntime PRIVATE ${CUDA_LIB})
endif()

file(GLOB TENSORFUNCTION_SRC fastdeploy/function/*.cc)
list(FILTER TENSORFUNCTION_SRC EXCLUDE REGEX ".*pybind.*")
if(WITH_CUDA)
    list(APPEND TENSORFUNCTION_SRC
        fastdeploy/function/cuda_cast.cu
    )
endif()
# hide tensor functions from shared library
add_library(FastDeploy_TensorFunction OBJECT ${TENSORFUNCTION_SRC})
target_include_directories(FastDeploy_TensorFunction PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(FastDeploy_TensorFunction PRIVATE Eigen3::Eigen)
if(WITH_CUDA)
    target_link_libraries(FastDeploy_TensorFunction PRIVATE ${CUDA_LIB})
endif()
if(MSVC)
    set_source_files_properties(
        fastdeploy/function/reduce.cc
        PROPERTIES COMPILE_OPTIONS "/bigobj"
    )
    target_compile_definitions(FastDeploy_TensorFunction PRIVATE EIGEN_STRONG_INLINE=inline)
endif()

file(GLOB VISION_COMMON_SRC fastdeploy/vision/common/*.cc fastdeploy/vision/common/processors/*.cc fastdeploy/vision/utils/*.cc)
list(FILTER VISION_COMMON_SRC EXCLUDE REGEX ".*pybind.*")
if(WITH_CUDA)
    list(APPEND VISION_COMMON_SRC
        fastdeploy/vision/common/processors/normalize_and_permute.cu
    )
endif()
add_library(FastDeploy_Vision_Common OBJECT ${VISION_COMMON_SRC})
if(WITH_CUDA)
    target_link_libraries(FastDeploy_Vision_Common PRIVATE ${CUDA_LIB})
endif()
target_link_libraries(FastDeploy_Vision_Common PUBLIC FastDeploy_Core ${OpenCV_LIBS} PRIVATE FastDeploy_TensorFunction)

file(GLOB_RECURSE VISION_OCR_SRC fastdeploy/vision/ocr/ppocr/*.cc)
list(FILTER VISION_OCR_SRC EXCLUDE REGEX ".*pybind.*")
add_library(FastDeploy_Vision_OCR OBJECT ${VISION_OCR_SRC})

target_link_libraries(FastDeploy_Vision_OCR PUBLIC FastDeploy_Vision_Common ${OpenCV_LIBS} PRIVATE FastDeploy_TensorFunction)

# export symbols
set_target_properties(FastDeploy_Core FastDeploy_Vision_OCR FastDeploy_Backend_ONNXRuntime PROPERTIES COMPILE_DEFINITIONS FASTDEPLOY_LIB)

# https://gitlab.kitware.com/cmake/cmake/-/issues/18090
# https://gitlab.kitware.com/cmake/cmake/-/issues/18935
add_library(fastdeploy_ppocr
    $<TARGET_OBJECTS:FastDeploy_Vision_OCR>
    $<TARGET_OBJECTS:FastDeploy_Vision_Common>
    $<TARGET_OBJECTS:FastDeploy_Core>
    $<TARGET_OBJECTS:FastDeploy_Backend_ONNXRuntime>
    $<TARGET_OBJECTS:FastDeploy_TensorFunction>
)
set_target_properties(
    fastdeploy_ppocr
    FastDeploy_Core
    FastDeploy_Backend_ONNXRuntime
    FastDeploy_TensorFunction
    FastDeploy_Vision_Common
    FastDeploy_Vision_OCR
    PROPERTIES
        CXX_STANDARD 17
)

target_include_directories(fastdeploy_ppocr INTERFACE 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>  # for build
    # Headers are installed to <prefix>/include (see the install() below).
    # CMAKE_INSTALL_INCLUDE is not defined in this project, so spell the
    # relative path out: an empty INSTALL_INTERFACE leaves the imported target
    # without any include directory for consumers.
    $<INSTALL_INTERFACE:include>  # for install
)

target_link_libraries(fastdeploy_ppocr PUBLIC ${OpenCV_LIBS} PRIVATE onnxruntime::onnxruntime)
if(WITH_CUDA)
    target_link_libraries(fastdeploy_ppocr PRIVATE ${CUDA_LIB})
endif()
if(ANDROID)
  target_link_libraries(fastdeploy_ppocr PRIVATE log)
endif()

install(TARGETS fastdeploy_ppocr EXPORT fastdeploy_ppocrConfig)
include(CMakePackageConfigHelpers)
install(EXPORT fastdeploy_ppocrConfig
    DESTINATION share/fastdeploy_ppocr
    FILE fastdeploy_ppocrTargets.cmake)
# A static build leaks $<LINK_ONLY:onnxruntime::onnxruntime> into the exported
# interface, so the package config has to help consumers materialize that
# target; ship the Find module it needs.
get_target_property(FASTDEPLOY_PPOCR_LIBRARY_TYPE fastdeploy_ppocr TYPE)
if(FASTDEPLOY_PPOCR_LIBRARY_TYPE STREQUAL "STATIC_LIBRARY")
    set(FASTDEPLOY_PPOCR_STATIC ON)
else()
    set(FASTDEPLOY_PPOCR_STATIC OFF)
endif()
install(FILES cmake/Findonnxruntime.cmake
    DESTINATION share/fastdeploy_ppocr/cmake)
configure_package_config_file(
    cmake/fastdeploy_ppocrConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/fastdeploy_ppocrConfig.cmake
    INSTALL_DESTINATION share/fastdeploy_ppocr)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/fastdeploy_ppocrConfig.cmake
    DESTINATION share/fastdeploy_ppocr)
install(
  DIRECTORY ${PROJECT_SOURCE_DIR}/fastdeploy
  DESTINATION include
  FILES_MATCHING
  PATTERN "*.h"
)