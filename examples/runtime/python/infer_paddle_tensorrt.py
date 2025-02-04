# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import fastdeploy as fd
import numpy as np

# 下载模型并解压
model_url = "https://bj.bcebos.com/fastdeploy/models/mobilenetv2.tgz"
fd.download_and_decompress(model_url)

option = fd.RuntimeOption()

option.set_model_path("mobilenetv2/inference.pdmodel",
                      "mobilenetv2/inference.pdiparams")

# **** GPU 配置 ***
option.use_cuda(0)
option.use_trt_backend()
# using TensorRT integrated in Paddle Inference
# option.enable_paddle_to_trt()

# 初始化构造runtime
runtime = fd.Runtime(option)

# 获取模型输入名
input_name = runtime.get_input_info(0).name

# 构造随机数据进行推理
results = runtime.infer({
    input_name: np.random.rand(1, 3, 224, 224).astype("float32")
})

print(results[0].shape)
