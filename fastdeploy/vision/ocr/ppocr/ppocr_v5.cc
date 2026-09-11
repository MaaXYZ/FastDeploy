// Copyright (c) 2024 PaddlePaddle Authors. All Rights Reserved.
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

#include "fastdeploy/vision/ocr/ppocr/ppocr_v5.h"

namespace fastdeploy {
namespace pipeline {

PPOCRv5::PPOCRv5(fastdeploy::vision::ocr::DBDetector* det_model,
                 fastdeploy::vision::ocr::Classifier* cls_model,
                 fastdeploy::vision::ocr::Recognizer* rec_model)
    : PPOCRv4(det_model, cls_model, rec_model) {}

PPOCRv5::PPOCRv5(fastdeploy::vision::ocr::DBDetector* det_model,
                 fastdeploy::vision::ocr::Recognizer* rec_model)
    : PPOCRv4(det_model, rec_model) {}

std::unique_ptr<PPOCRv5> PPOCRv5::Clone() const {
  std::unique_ptr<PPOCRv5> clone_model = utils::make_unique<PPOCRv5>(PPOCRv5(*this));
  clone_model->detector_ = detector_->Clone().release();
  if (classifier_ != nullptr) {
    clone_model->classifier_ = classifier_->Clone().release();
  }
  clone_model->recognizer_ = recognizer_->Clone().release();
  return clone_model;
}

}  // namespace pipeline
}  // namespace fastdeploy
