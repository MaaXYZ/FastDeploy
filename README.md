# FastDeploy

This is a stripped-down version of [PaddlePaddle/FastDeploy](https://github.com/PaddlePaddle/FastDeploy) and [MaaAssistantArknights/FastDeploy](https://github.com/MaaAssistantArknights/FastDeploy).

## Key modifications

### For PaddlePaddle/FastDeploy

* ~~Removed unused components~~
* Use system library (CMake `find_package`) only
* Library name changed to `fastdeploy_ppocr`

### For MaaAssistantArknights/FastDeploy

* Connect to historical commits for later updates
* Fixed reading of files instead of passing them through memory
