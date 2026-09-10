#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-platform build and packaging script for FastDeploy (fastdeploy_ppocr).
Usage:
    python scripts/build.py --target [macos-arm64 | linux-x64 | windows-x64 | windows-arm64 | android-arm64 | python-wheel]
"""

import os
import sys
import shutil
import argparse
import subprocess
import urllib.request
import zipfile
import tarfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEPS_DIR = os.path.join(PROJECT_ROOT, "deps")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
ORT_VERSION = "1.29.0"

def log(msg):
    print(f"\n[build.py] ===> {msg}", flush=True)

def run_cmd(cmd, cwd=PROJECT_ROOT, env=None):
    log(f"Running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    ret = subprocess.run(cmd, cwd=cwd, env=cmd_env, shell=isinstance(cmd, str))
    if ret.returncode != 0:
        print(f"\n[build.py] Error: command failed with return code {ret.returncode}", file=sys.stderr)
        sys.exit(ret.returncode)

def download_file(url, target_path):
    if os.path.exists(target_path):
        log(f"File already exists: {target_path}")
        return
    log(f"Downloading {url} to {target_path} ...")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(target_path, "wb") as out_file:
        shutil.copyfileobj(resp, out_file)
    log(f"Download complete: {target_path}")

def extract_archive(archive_path, extract_to):
    log(f"Extracting {archive_path} to {extract_to} ...")
    os.makedirs(extract_to, exist_ok=True)
    if archive_path.endswith(".zip") or archive_path.endswith(".nupkg") or archive_path.endswith(".aar"):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        # Fallback for 7z / exe on Windows
        if shutil.which("7z"):
            run_cmd(["7z", "x", archive_path, f"-o{extract_to}", "-y"])
        else:
            raise RuntimeError(f"Unsupported archive or 7z not installed: {archive_path}")

def package_dist(target_name, fmt="tar.gz"):
    log(f"Packaging dist directory to fastdeploy_ppocr-{target_name}.{fmt} ...")
    pkg_name = f"fastdeploy_ppocr-{target_name}"
    if fmt == "tar.gz":
        archive_file = os.path.join(PROJECT_ROOT, f"{pkg_name}.tar.gz")
        with tarfile.open(archive_file, "w:gz") as tar:
            for item in os.listdir(DIST_DIR):
                item_path = os.path.join(DIST_DIR, item)
                tar.add(item_path, arcname=item)
    elif fmt == "zip":
        archive_file = os.path.join(PROJECT_ROOT, f"{pkg_name}.zip")
        shutil.make_archive(os.path.join(PROJECT_ROOT, pkg_name), 'zip', DIST_DIR)
    log(f"Artifact created: {pkg_name}.{fmt}")

def clean():
    for d in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(d):
            log(f"Cleaning {d} ...")
            shutil.rmtree(d, ignore_errors=True)

# -------------------------------------------------------------------------
# Targets
# -------------------------------------------------------------------------

def build_macos_arm64(args):
    clean()
    os.makedirs(BUILD_DIR, exist_ok=True)
    # Query brew prefix
    def get_brew_prefix(pkg):
        res = subprocess.run(["brew", "--prefix", pkg], capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else f"/opt/homebrew/opt/{pkg}"

    # Prefer opencv@4 over opencv for API compatibility
    opencv_prefix = None
    for pkg in ["opencv@4", "opencv"]:
        prefix = get_brew_prefix(pkg)
        if os.path.exists(prefix):
            opencv_prefix = prefix
            break
    if not opencv_prefix:
        opencv_prefix = get_brew_prefix("opencv@4")

    ort_prefix = get_brew_prefix("onnxruntime")
    eigen_prefix = get_brew_prefix("eigen")

    cmake_args = [
        "cmake", "..", "-G", "Ninja",
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        f"-DCMAKE_INSTALL_PREFIX={DIST_DIR}",
        f"-DCMAKE_PREFIX_PATH={opencv_prefix};{ort_prefix};{eigen_prefix}",
        "-DWITH_CUDA=OFF"
    ]
    opencv_cmake_dir = os.path.join(opencv_prefix, "lib", "cmake", "opencv4")
    if os.path.exists(opencv_cmake_dir):
        cmake_args.append(f"-DOpenCV_DIR={opencv_cmake_dir}")
    run_cmd(cmake_args, cwd=BUILD_DIR)
    run_cmd(["ninja"], cwd=BUILD_DIR)
    run_cmd(["cmake", "--install", ".", "--prefix", DIST_DIR], cwd=BUILD_DIR)
    package_dist("macos-arm64", fmt="tar.gz")

def build_linux_x64(args):
    clean()
    os.makedirs(BUILD_DIR, exist_ok=True)
    ort_tar = os.path.join(DEPS_DIR, f"onnxruntime-linux-x64-{ORT_VERSION}.tgz")
    ort_dir = os.path.join(DEPS_DIR, f"onnxruntime-linux-x64-{ORT_VERSION}")
    if not os.path.exists(ort_dir):
        download_file(f"https://github.com/microsoft/onnxruntime/releases/download/v{ORT_VERSION}/onnxruntime-linux-x64-{ORT_VERSION}.tgz", ort_tar)
        extract_archive(ort_tar, DEPS_DIR)

    cmake_args = [
        "cmake", "..", "-G", "Ninja",
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        f"-DCMAKE_INSTALL_PREFIX={DIST_DIR}",
        f"-DCMAKE_PREFIX_PATH={ort_dir};/usr/include/eigen3",
        "-DWITH_CUDA=OFF"
    ]
    run_cmd(cmake_args, cwd=BUILD_DIR)
    run_cmd(["ninja"], cwd=BUILD_DIR)
    run_cmd(["cmake", "--install", ".", "--prefix", DIST_DIR], cwd=BUILD_DIR)
    package_dist("linux-x64", fmt="tar.gz")

def build_windows_x64(args):
    clean()
    os.makedirs(BUILD_DIR, exist_ok=True)
    # 1. Eigen3
    eigen_zip = os.path.join(DEPS_DIR, "eigen.zip")
    eigen_dir = os.path.join(DEPS_DIR, "eigen-3.4.0")
    if not os.path.exists(eigen_dir):
        download_file("https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip", eigen_zip)
        extract_archive(eigen_zip, DEPS_DIR)

    # 2. ONNXRuntime Windows x64 (official GitHub release)
    ort_zip = os.path.join(DEPS_DIR, f"onnxruntime-win-x64-{ORT_VERSION}.zip")
    ort_dir = os.path.join(DEPS_DIR, f"onnxruntime-win-x64-{ORT_VERSION}")
    if not os.path.exists(ort_dir):
        download_file(f"https://github.com/microsoft/onnxruntime/releases/download/v{ORT_VERSION}/onnxruntime-win-x64-{ORT_VERSION}.zip", ort_zip)
        extract_archive(ort_zip, DEPS_DIR)

    # 3. OpenCV
    opencv_exe = os.path.join(DEPS_DIR, "opencv.exe")
    opencv_root = os.path.join(DEPS_DIR, "opencv", "build")
    if not os.path.exists(opencv_root):
        download_file("https://github.com/opencv/opencv/releases/download/4.9.0/opencv-4.9.0-windows.exe", opencv_exe)
        extract_archive(opencv_exe, DEPS_DIR)

    opencv_vc16_lib = os.path.join(opencv_root, "x64", "vc16", "lib")
    opencv_dir = opencv_vc16_lib if os.path.exists(opencv_vc16_lib) else opencv_root

    cmake_args = [
        "cmake", "..", "-G", "Ninja",
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        f"-DCMAKE_INSTALL_PREFIX={DIST_DIR}",
        f"-DOpenCV_DIR={opencv_dir}",
        "-DOpenCV_RUNTIME=vc16",
        f"-DCMAKE_PREFIX_PATH={ort_dir};{eigen_dir}",
        "-DWITH_CUDA=OFF"
    ]
    run_cmd(cmake_args, cwd=BUILD_DIR)
    run_cmd(["ninja"], cwd=BUILD_DIR)
    run_cmd(["cmake", "--install", ".", "--prefix", DIST_DIR, "--config", args.build_type], cwd=BUILD_DIR)

    # Copy runtime DLLs to output bin directory
    dist_bin = os.path.join(DIST_DIR, "bin")
    os.makedirs(dist_bin, exist_ok=True)
    ort_lib_dir = os.path.join(ort_dir, "lib")
    if os.path.exists(ort_lib_dir):
        for f in os.listdir(ort_lib_dir):
            if f.endswith(".dll"):
                shutil.copy2(os.path.join(ort_lib_dir, f), dist_bin)
    opencv_bin = os.path.join(opencv_root, "x64", "vc16", "bin")
    if os.path.exists(opencv_bin):
        for f in os.listdir(opencv_bin):
            if f.endswith(".dll"):
                shutil.copy2(os.path.join(opencv_bin, f), dist_bin)

    package_dist("windows-x64", fmt="zip")

def build_android_arm64(args):
    clean()
    os.makedirs(BUILD_DIR, exist_ok=True)
    ndk_home = os.environ.get("ANDROID_NDK_LATEST_HOME") or os.environ.get("ANDROID_NDK_HOME") or os.environ.get("ANDROID_NDK_ROOT")
    if not ndk_home or not os.path.exists(ndk_home):
        raise RuntimeError(f"Android NDK not found in environment (checked ANDROID_NDK_LATEST_HOME, ANDROID_NDK_HOME, ANDROID_NDK_ROOT)")

    # 1. Eigen3
    eigen_zip = os.path.join(DEPS_DIR, "eigen.zip")
    eigen_dir = os.path.join(DEPS_DIR, "eigen-3.4.0")
    if not os.path.exists(eigen_dir):
        download_file("https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip", eigen_zip)
        extract_archive(eigen_zip, DEPS_DIR)

    # 2. OpenCV Android
    opencv_zip = os.path.join(DEPS_DIR, "opencv-android.zip")
    opencv_dir = os.path.join(DEPS_DIR, "OpenCV-android-sdk", "sdk", "native", "jni")
    if not os.path.exists(opencv_dir):
        download_file("https://github.com/opencv/opencv/releases/download/4.9.0/opencv-4.9.0-android-sdk.zip", opencv_zip)
        extract_archive(opencv_zip, DEPS_DIR)

    # 3. ORT Android
    ort_aar = os.path.join(DEPS_DIR, f"ort-android-{ORT_VERSION}.aar")
    ort_extract_dir = os.path.join(DEPS_DIR, f"ort-android-{ORT_VERSION}")
    ort_include_dir = os.path.join(ort_extract_dir, "headers")
    ort_lib_file = os.path.join(ort_extract_dir, "jni", "arm64-v8a", "libonnxruntime.so")

    if not os.path.exists(ort_lib_file):
        download_file(f"https://repo1.maven.org/maven2/com/microsoft/onnxruntime/onnxruntime-android/{ORT_VERSION}/onnxruntime-android-{ORT_VERSION}.aar", ort_aar)
        extract_archive(ort_aar, ort_extract_dir)

    toolchain = os.path.join(ndk_home, "build", "cmake", "android.toolchain.cmake")
    cmake_args = [
        "cmake", "..", "-G", "Ninja",
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        "-DANDROID_ABI=arm64-v8a",
        "-DANDROID_PLATFORM=android-24",
        "-DANDROID_STL=c++_shared",
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        f"-DCMAKE_INSTALL_PREFIX={DIST_DIR}",
        f"-DOpenCV_DIR={opencv_dir}",
        f"-Donnxruntime_INCLUDE_DIR={ort_include_dir}",
        f"-Donnxruntime_LIBRARY={ort_lib_file}",
        f"-DCMAKE_PREFIX_PATH={eigen_dir}",
        "-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH",
        "-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH",
        "-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH",
        "-DWITH_CUDA=OFF"
    ]
    run_cmd(cmake_args, cwd=BUILD_DIR)
    run_cmd(["ninja"], cwd=BUILD_DIR)
    run_cmd(["cmake", "--install", ".", "--prefix", DIST_DIR], cwd=BUILD_DIR)
    package_dist("android-arm64", fmt="tar.gz")

def main():
    parser = argparse.ArgumentParser(description="FastDeploy Build & Package Helper")
    parser.add_argument("--target", required=True,
                        choices=["macos-arm64", "linux-x64", "windows-x64", "android-arm64"],
                        help="Target platform to build for")
    parser.add_argument("--build-type", default="Release", help="CMake build type (Release, Debug, etc.)")
    args = parser.parse_args()

    targets = {
        "macos-arm64": build_macos_arm64,
        "linux-x64": build_linux_x64,
        "windows-x64": build_windows_x64,
        "android-arm64": build_android_arm64,
    }
    targets[args.target](args)

if __name__ == "__main__":
    main()

