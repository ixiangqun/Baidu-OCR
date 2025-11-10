#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找出所有处理失败的文件
通过对比原始图片和OCR结果来找出所有失败文件
"""

import os
from pathlib import Path
import glob

def find_failed_files():
    """找出所有处理失败的文件"""

    # 原始图片目录
    original_dir = Path("/Users/lixiangqun/Work/AI Positioning/老板案例/案例照片2")

    # OCR结果目录
    ocr_result_dir = Path("baidu_ocr_results")

    # 获取所有原始图片文件
    original_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']:
        original_files.extend(original_dir.glob(ext))
        original_files.extend(original_dir.glob(ext.upper()))

    # 获取所有OCR结果文件
    result_files = list(ocr_result_dir.glob("*_baidu.md"))

    # 提取结果文件对应的原始文件名
    processed_files = set()
    for result_file in result_files:
        # 从结果文件名提取原始文件名
        # 20151202_212224_baidu.md -> 20151202_212224.jpg
        base_name = result_file.stem.replace('_baidu', '')
        # 尝试匹配可能的扩展名
        for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.JPG', '.JPEG', '.PNG', '.BMP', '.TIFF']:
            possible_file = base_name + ext
            if (original_dir / possible_file).exists():
                processed_files.add(possible_file)
                break

    # 找出未处理的文件（失败文件）
    failed_files = []
    for original_file in original_files:
        if original_file.name not in processed_files:
            failed_files.append(original_file.name)

    # 排序
    failed_files.sort()

    print(f"原始图片总数: {len(original_files)}")
    print(f"成功处理: {len(processed_files)}")
    print(f"失败文件: {len(failed_files)}")
    print("\n所有失败文件:")
    print("=" * 50)

    for i, filename in enumerate(failed_files, 1):
        print(f"{i:2d}. {filename}")

    # 保存到文件
    with open('complete_failed_files.txt', 'w', encoding='utf-8') as f:
        for filename in failed_files:
            f.write(filename + '\n')

    print(f"\n失败文件列表已保存到 complete_failed_files.txt")
    print(f"总计: {len(failed_files)} 个失败文件")

    return failed_files

if __name__ == "__main__":
    failed_files = find_failed_files()