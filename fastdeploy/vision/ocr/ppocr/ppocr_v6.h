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

#pragma once

#include "fastdeploy/vision/ocr/ppocr/ppocr_v5.h"

namespace fastdeploy {
/** \brief This pipeline can launch detection model, classification model and recognition model sequentially. All OCR pipeline APIs are defined inside this namespace.
 *
 */
namespace pipeline {
/*! @brief PPOCRv6 is used to load PP-OCRv6 series models provided by PaddleOCR.
 *
 *  Note: For PP-OCRv6, PaddleOCR officially recommends detector postprocessing parameters:
 *  - det_db_thresh = 0.2
 *  - det_db_box_thresh = 0.45
 *  - det_db_unclip_ratio = 1.4
 *  - det_db_max_candidates = 3000
 *  To avoid overwriting custom configurations, PPOCRv6 does not modify DBDetector
 *  parameters in its constructor. Call det_model->GetPostprocessor().SetDetDB*()
 *  before or after pipeline construction if needed.
 */
class FASTDEPLOY_DECL PPOCRv6 : public PPOCRv5 {
 public:
   /** \brief Set up the detection model path, classification model path and recognition model path respectively.
   *
   * \param[in] det_model Path of detection model, e.g ./ch_PP-OCRv6_det_infer
   * \param[in] cls_model Path of classification model, e.g ./ch_ppocr_mobile_v2.0_cls_infer
   * \param[in] rec_model Path of recognition model, e.g ./ch_PP-OCRv6_rec_infer
   */
  PPOCRv6(fastdeploy::vision::ocr::DBDetector* det_model,
          fastdeploy::vision::ocr::Classifier* cls_model,
          fastdeploy::vision::ocr::Recognizer* rec_model);
  /** \brief Classification model is optional, so this function is set up the detection model path and recognition model path respectively.
   *
   * \param[in] det_model Path of detection model, e.g ./ch_PP-OCRv6_det_infer
   * \param[in] rec_model Path of recognition model, e.g ./ch_PP-OCRv6_rec_infer
   */
  PPOCRv6(fastdeploy::vision::ocr::DBDetector* det_model,
          fastdeploy::vision::ocr::Recognizer* rec_model);

  /** \brief Clone a new PPOCRv6 with less memory usage when multiple instances of the same model are created
   *
   * \return new PPOCRv6* type unique pointer
   */
  std::unique_ptr<PPOCRv6> Clone() const;
};

}  // namespace pipeline

}  // namespace fastdeploy

