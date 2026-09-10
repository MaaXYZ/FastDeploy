// Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.
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

#include "fastdeploy/vision/ocr/ppocr/ppocr_v4.h"

namespace fastdeploy {
/** \brief This pipeline can launch detection model, classification model and recognition model sequentially. All OCR pipeline APIs are defined inside this namespace.
 *
 */
namespace pipeline {
/*! @brief PPOCRv5 is used to load PP-OCRv5 series models provided by PaddleOCR.
 */
class FASTDEPLOY_DECL PPOCRv5 : public PPOCRv4 {
 public:
   /** \brief Set up the detection model path, classification model path and recognition model path respectively.
   *
   * \param[in] det_model Path of detection model, e.g ./ch_PP-OCRv5_det_infer
   * \param[in] cls_model Path of classification model, e.g ./ch_ppocr_mobile_v2.0_cls_infer
   * \param[in] rec_model Path of recognition model, e.g ./ch_PP-OCRv5_rec_infer
   */
  PPOCRv5(fastdeploy::vision::ocr::DBDetector* det_model,
          fastdeploy::vision::ocr::Classifier* cls_model,
          fastdeploy::vision::ocr::Recognizer* rec_model)
          : PPOCRv4(det_model, cls_model, rec_model) {
    auto preprocess_shape = recognizer_->GetPreprocessor().GetRecImageShape();
    preprocess_shape[1] = 48;
    recognizer_->GetPreprocessor().SetRecImageShape(preprocess_shape);
    if (detector_ != nullptr) {
      detector_->GetPostprocessor().SetDetDBThresh(0.3);
      detector_->GetPostprocessor().SetDetDBBoxThresh(0.6);
      detector_->GetPostprocessor().SetDetDBUnclipRatio(1.5);
      detector_->GetPostprocessor().SetDetDBMaxCandidates(1000);
    }
  }
  /** \brief Classification model is optional, so this function is set up the detection model path and recognition model path respectively.
   *
   * \param[in] det_model Path of detection model, e.g ./ch_PP-OCRv5_det_infer
   * \param[in] rec_model Path of recognition model, e.g ./ch_PP-OCRv5_rec_infer
   */
  PPOCRv5(fastdeploy::vision::ocr::DBDetector* det_model,
          fastdeploy::vision::ocr::Recognizer* rec_model)
          : PPOCRv4(det_model, rec_model) {
    auto preprocess_shape = recognizer_->GetPreprocessor().GetRecImageShape();
    preprocess_shape[1] = 48;
    recognizer_->GetPreprocessor().SetRecImageShape(preprocess_shape);
    if (detector_ != nullptr) {
      detector_->GetPostprocessor().SetDetDBThresh(0.3);
      detector_->GetPostprocessor().SetDetDBBoxThresh(0.6);
      detector_->GetPostprocessor().SetDetDBUnclipRatio(1.5);
      detector_->GetPostprocessor().SetDetDBMaxCandidates(1000);
    }
  }

  /** \brief Clone a new PPOCRv5 with less memory usage when multiple instances of the same model are created
   *
   * \return new PPOCRv5* type unique pointer
   */
  std::unique_ptr<PPOCRv5> Clone() const {
    std::unique_ptr<PPOCRv5> clone_model = utils::make_unique<PPOCRv5>(PPOCRv5(*this));
    clone_model->detector_ = detector_->Clone().release();
    if (classifier_ != nullptr) {
      clone_model->classifier_ = classifier_->Clone().release();
    }
    clone_model->recognizer_ = recognizer_->Clone().release();
    return clone_model;
  }
};

}  // namespace pipeline

namespace application {
namespace ocrsystem {
  typedef pipeline::PPOCRv5 PPOCRSystemv5;
}  // namespace ocrsystem
}  // namespace application

}  // namespace fastdeploy
