// Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
#pragma once

#ifndef FASTDEPLOY_LIB
/* #undef FASTDEPLOY_LIB */
#endif

#ifndef ENABLE_PADDLE2ONNX
/* #undef ENABLE_PADDLE2ONNX */
#endif

#ifndef ENABLE_ORT_BACKEND
#define ENABLE_ORT_BACKEND
#endif

#ifndef ENABLE_PADDLE_BACKEND
/* #undef ENABLE_PADDLE_BACKEND */
#endif

#ifndef ENABLE_POROS_BACKEND
/* #undef ENABLE_POROS_BACKEND */
#endif

#ifndef ENABLE_OPENVINO_BACKEND
/* #undef ENABLE_OPENVINO_BACKEND */
#endif

#ifndef WITH_CUDA
/* #undef WITH_CUDA */
#endif

#ifndef WITH_KUNLUNXIN
/* #undef WITH_KUNLUNXIN */
#endif

#ifndef WITH_DIRECTML
#define WITH_DIRECTML
#endif

#ifndef WITH_COREML
#define WITH_COREML
#endif

#ifndef ENABLE_TRT_BACKEND
/* #undef ENABLE_TRT_BACKEND */
#endif

#ifndef ENABLE_VISION
#define ENABLE_VISION
#endif

#ifndef ENABLE_FLYCV
/* #undef ENABLE_FLYCV */
#endif

#ifndef ENABLE_TEXT
/* #undef ENABLE_TEXT */
#endif

#ifndef ENABLE_BENCHMARK
/* #undef ENABLE_BENCHMARK */
#endif

#ifndef ENABLE_HORIZON_BACKEND
/* #undef ENABLE_HORIZON_BACKEND */
#endif

#ifndef ENABLE_TVM_BACKEND
/* #undef ENABLE_TVM_BACKEND */
#endif
