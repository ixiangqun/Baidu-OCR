#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新处理因API频率限制失败的文件
使用较慢的速度避免触发频率限制
"""

import os
import time
from pathlib import Path
from datetime import datetime
from baidu_ocr_integration import BaiduOCRProcessor
from typing import List, Dict

class RetryFailedFiles:
    """重试失败文件处理器"""

    def __init__(self, api_key: str, secret_key: str):
        """初始化处理器"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.processor = BaiduOCRProcessor(api_key, secret_key)
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0
        }

    def process_with_retry(self, image_file: str, output_file: str, max_retries: int = 3) -> Dict:
        """带重试的处理单个图片"""
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # 添加延迟以避免频率限制
                if attempt > 0:
                    delay = 2 ** attempt  # 指数退避
                    print(f"⏳ 等待 {delay} 秒后重试...")
                    time.sleep(delay)

                # 使用高精度模式处理
                success = self.processor.process_single_image(image_file, output_file, 'accurate')

                processing_time = time.time() - start_time

                if success:
                    # 读取处理结果
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        char_count = len(content)
                        word_count = len(content.split())
                    except:
                        char_count = 0
                        word_count = 0

                    self.stats['success_count'] += 1
                    return {
                        'success': True,
                        'image_file': image_file,
                        'output_file': output_file,
                        'processing_time': processing_time,
                        'char_count': char_count,
                        'word_count': word_count,
                        'error': None,
                        'retries': attempt
                    }
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️  第{attempt + 1}次尝试失败，继续重试...")
                        continue
                    else:
                        self.stats['failed_count'] += 1
                        return {
                            'success': False,
                            'image_file': image_file,
                            'output_file': output_file,
                            'processing_time': processing_time,
                            'char_count': 0,
                            'word_count': 0,
                            'error': '百度OCR处理失败',
                            'retries': attempt
                        }

            except Exception as e:
                error_msg = str(e)
                if 'qps request limit reached' in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"⚠️  API频率限制，第{attempt + 1}次尝试失败，继续重试...")
                        continue

                if attempt < max_retries - 1:
                    print(f"⚠️  第{attempt + 1}次尝试失败: {error_msg}")
                    continue
                else:
                    self.stats['failed_count'] += 1
                    return {
                        'success': False,
                        'image_file': image_file,
                        'output_file': output_file,
                        'processing_time': 0,
                        'char_count': 0,
                        'word_count': 0,
                        'error': error_msg,
                        'retries': attempt
                    }

    def retry_failed_files(self, failed_files: List[str], input_dir: str, output_dir: str):
        """重试处理失败的文件"""
        print("🔄 重试处理API频率限制失败的文件")
        print("=" * 60)
        print(f"📁 输入目录: {input_dir}")
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 失败文件数: {len(failed_files)}")
        print(f"⏱️  使用延迟重试策略避免频率限制")

        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        results = []

        print(f"\n🔄 开始重试处理...")
        print("=" * 60)

        for i, filename in enumerate(failed_files, 1):
            input_path = Path(input_dir) / filename
            output_path = Path(output_dir) / f"{Path(filename).stem}_baidu_retry.md"

            if not input_path.exists():
                print(f"⚠️  文件不存在: {filename}")
                continue

            print(f"[{i:2d}/{len(failed_files)}] 重试: {filename}")

            # 处理文件（带重试）
            result = self.process_with_retry(str(input_path), str(output_path))
            results.append(result)
            self.stats['total_processed'] += 1

            if result['success']:
                print(f"   ✅ 成功 - {result['char_count']}字符 (重试{result['retries']}次)")
            else:
                print(f"   ❌ 失败 - {result['error']} (重试{result['retries']}次)")

        # 生成统计
        self.generate_retry_report(results, output_dir)

        print(f"\n🎉 重试处理完成!")
        print("=" * 60)
        print(f"📊 重试统计:")
        print(f"   总处理: {self.stats['total_processed']}")
        print(f"   成功: {self.stats['success_count']}")
        print(f"   失败: {self.stats['failed_count']}")
        print(f"   成功率: {(self.stats['success_count']/self.stats['total_processed']*100):.1f}%")

        return results

    def generate_retry_report(self, results: List[dict], output_dir: str):
        """生成重试报告"""
        report_file = Path(output_dir) / "retry_report.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# API频率限制失败文件重试报告\n\n")
            f.write(f"重试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 总体统计
            f.write("## 重试统计\n\n")
            f.write(f"- 总处理文件: {self.stats['total_processed']}\n")
            f.write(f"- 成功处理: {self.stats['success_count']}\n")
            f.write(f"- 处理失败: {self.stats['failed_count']}\n")
            f.write(f"- 成功率: {(self.stats['success_count']/self.stats['total_processed']*100):.1f}%\n\n")

            # 成功案例
            success_results = [r for r in results if r['success']]
            if success_results:
                f.write("## 成功案例\n\n")
                for result in success_results:
                    f.write(f"### {Path(result['image_file']).name}\n")
                    f.write(f"字符数: {result['char_count']}\n")
                    f.write(f"单词数: {result['word_count']}\n")
                    f.write(f"处理时间: {result['processing_time']:.2f}秒\n")
                    f.write(f"重试次数: {result['retries'] + 1}\n\n")

            # 失败案例
            failed_results = [r for r in results if not r['success']]
            if failed_results:
                f.write("## 失败案例\n\n")
                for result in failed_results:
                    f.write(f"### {Path(result['image_file']).name}\n")
                    f.write(f"错误信息: {result['error']}\n")
                    f.write(f"重试次数: {result['retries'] + 1}\n\n")

            f.write("---\n")
            f.write(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        print(f"📄 重试报告已保存: {report_file}")

def main():
    """主函数"""
    print("🔄 API频率限制失败文件重试处理器")
    print("=" * 60)

    # API凭据
    api_key = "Y5iCqs919ZJP1Og1fEQqGsSW"
    secret_key = "c8La43KW46QInpCD3muLZIdtc1DiKpKa"

    # 输入输出目录
    input_dir = "all_failed_temp"  # 使用之前修复后的临时文件
    output_dir = "retry_results"

    # 之前因API频率限制失败的文件（从完整处理结果中提取）
    failed_files = [
        "20151202_224237.jpg",   # QPS限制
        "20151203_031924.jpg",   # QPS限制
        "20151203_034626.jpg",   # QPS限制
        "20151203_041427.jpg",   # QPS限制
        "20151203_042024.jpg"    # QPS限制
    ]

    print(f"📁 输入目录: {input_dir}")
    print(f"📁 输出目录: {output_dir}")
    print(f"📊 重试文件数: {len(failed_files)}")

    # 初始化处理器
    retry_processor = RetryFailedFiles(api_key, secret_key)

    # 开始重试处理
    results = retry_processor.retry_failed_files(failed_files, input_dir, output_dir)

    # 显示最终结果
    print(f"\n🎯 重试处理完成!")
    print(f"📁 结果保存在: {output_dir}/")
    print(f"📄 详细报告: {output_dir}/retry_report.md")

    # 计算改进
    if retry_processor.stats['total_processed'] > 0:
        recovery_rate = (retry_processor.stats['success_count'] / retry_processor.stats['total_processed']) * 100
        print(f"\n📈 重试效果:")
        print(f"   重试成功率: {recovery_rate:.1f}%")
        print(f"   预计整体成功率提升: +{(recovery_rate * len(failed_files) / 428):.1f}%")

if __name__ == "__main__":
    from typing import List
    main()