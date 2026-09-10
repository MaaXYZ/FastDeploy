#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2024 PaddlePaddle Authors. All Rights Reserved.
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

import argparse
import json
import os
import sys


def unquote_yaml_scalar(val):
    if len(val) >= 2 and val.startswith("'") and val.endswith("'"):
        # YAML single quotes: escaped quote is ''
        return val[1:-1].replace("''", "'")
    if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
        # YAML double quotes: standard JSON/C-style escape
        try:
            return json.loads(val)
        except Exception:
            return val[1:-1]
    return val


def extract_dict(yaml_file, output_file):
    if not os.path.exists(yaml_file):
        raise FileNotFoundError(f"YAML file not found: {yaml_file}")

    characters = []

    # Try PyYAML first if installed
    try:
        import yaml
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            # Check PostProcess -> character_dict
            post_process = data.get("PostProcess", {})
            if isinstance(post_process, dict) and "character_dict" in post_process:
                characters = post_process["character_dict"]
            elif "character_dict" in data:
                characters = data["character_dict"]
    except ImportError:
        pass

    # Fallback to pure-Python YAML list parser if PyYAML unavailable or not found
    if not characters:
        with open(yaml_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_character_dict = False
        dict_indent = None

        for line in lines:
            line_str = line.rstrip("\r\n")
            # Only strip ASCII space/tab indentation from left to preserve Unicode characters
            lstripped = line_str.lstrip(" \t")

            if lstripped.startswith("character_dict:"):
                in_character_dict = True
                dict_indent = len(line_str) - len(lstripped)
                continue

            if in_character_dict:
                if not lstripped:
                    continue
                current_indent = len(line_str) - len(lstripped)
                if current_indent <= dict_indent and not lstripped.startswith("-"):
                    # Exited character_dict section
                    break

                # Check if list item under character_dict
                if lstripped.startswith("- "):
                    raw_val = lstripped[2:]
                    char_val = unquote_yaml_scalar(raw_val)
                    characters.append(char_val)
                elif lstripped == "-":
                    characters.append("")

    if not characters:
        raise ValueError(f"No character_dict found in {yaml_file}")

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for ch in characters:
            f.write(f"{ch}\n")

    print(f"Successfully extracted {len(characters)} characters to: {output_file}")
    if characters:
        print(f"  First 5 items: {characters[:5]}")
        print(f"  Last 5 items:  {characters[-5:]}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract character dictionary from PP-OCRv5/v6 inference.yml"
    )
    parser.add_argument(
        "--yaml_file",
        "-y",
        required=True,
        help="Path to inference.yml containing character_dict",
    )
    parser.add_argument(
        "--output_file",
        "-o",
        default="ppocr_keys.txt",
        help="Path to output dictionary text file (default: ppocr_keys.txt)",
    )
    args = parser.parse_args()

    extract_dict(args.yaml_file, args.output_file)


if __name__ == "__main__":
    main()
