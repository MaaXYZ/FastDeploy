# FastDeploy

This is a stripped-down version of [PaddlePaddle/FastDeploy@v1](https://github.com/PaddlePaddle/FastDeploy/tree/release/1.1.0) and [MaaAssistantArknights/FastDeploy](https://github.com/MaaAssistantArknights/FastDeploy).

## Key modifications

* ~~Removed unused components and dead code, focusing on `fastdeploy_ppocr`~~
* Use system libraries (CMake `find_package`) only
* Support in-memory model and dictionary loading
* Reorganized project layout (`bindings/`, `services/`)
* Add support for PP-OCR v5 and v6
* Add multi-platform build script (`scripts/build.py`)