cmake_minimum_required(VERSION 3.20)
project(fastdeploy_ppocr CXX)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

find_package(OpenCV COMPONENTS core imgproc)
find_package(onnxruntime REQUIRED)
find_package(Eigen3 REQUIRED)
message("OpenCV_LIBS: ${OpenCV_LIBS} ${OPENCV_core_FOUND} ${OPENCV_WORLD_FOUND}")

option(WITH_CUDA "Whether WITH_GPU=ON, will enable onnxruntime-gpu/paddle-infernce-gpu/poros-gpu" OFF)
option(PRINT_INFO "Print more debug info while running" OFF)

if(WITH_CUDA)
    add_definitions (-Wno-format-security)
    enable_language(CUDA)
    include(cmake/cuda.cmake)
    message(STATUS "CUDA compiler: ${CMAKE_CUDA_COMPILER}, version: ${CMAKE_CUDA_COMPILER_ID} ${CMAKE_CUDA_COMPILER_VERSION}")
    add_definitions(-DWITH_GPU)
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
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDE}>  # for install
)

target_link_libraries(fastdeploy_ppocr PUBLIC ${OpenCV_LIBS} PRIVATE onnxruntime::onnxruntime)
if(WITH_CUDA)
    target_link_libraries(fastdeploy_ppocr PRIVATE ${CUDA_LIB})
endif()
if(ANDROID)
  target_link_libraries(fastdeploy_ppocr PRIVATE log)
endif()

install(TARGETS fastdeploy_ppocr EXPORT fastdeploy_ppocrConfig)
install(EXPORT fastdeploy_ppocrConfig DESTINATION share/fastdeploy_ppocr)
install(
  DIRECTORY ${PROJECT_SOURCE_DIR}/fastdeploy
  DESTINATION ${CMAKE_INSTALL_PREFIX}/include
  FILES_MATCHING
  PATTERN "*.h"
)