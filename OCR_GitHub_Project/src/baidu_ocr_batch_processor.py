#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度OCR批量处理器
使用百度OCR重新识别所有图片
"""

import os
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from baidu_ocr_integration import BaiduOCRProcessor
import concurrent.futures
from tqdm import tqdm

class BaiduOCRBatchProcessor:
    """百度OCR批量处理器"""

    def __init__(self, api_key: str, secret_key: str):
        """初始化处理器"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.processor = BaiduOCRProcessor(api_key, secret_key)
        self.results = []
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0

    def get_image_files(self, directory: str) -> List[str]:
        """获取目录中的所有图片文件"""
        path = Path(directory)
        image_files = []

        for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            image_files.extend(path.glob(f"*{ext}"))
            image_files.extend(path.glob(f"*{ext.upper()}"))

        return [str(f) for f in sorted(image_files)]

    def process_single_image_safe(self, image_file: str, output_file: str) -> Dict:
        """安全处理单个图片，包含错误处理"""
        try:
            start_time = time.time()

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

                self.success_count += 1
                return {
                    'success': True,
                    'image_file': image_file,
                    'output_file': output_file,
                    'processing_time': processing_time,
                    'char_count': char_count,
                    'word_count': word_count,
                    'error': None
                }
            else:
                self.failed_count += 1
                return {
                    'success': False,
                    'image_file': image_file,
                    'output_file': output_file,
                    'processing_time': processing_time,
                    'char_count': 0,
                    'word_count': 0,
                    'error': '百度OCR处理失败'
                }

        except Exception as e:
            self.failed_count += 1
            return {
                'success': False,
                'image_file': image_file,
                'output_file': output_file,
                'processing_time': 0,
                'char_count': 0,
                'word_count': 0,
                'error': str(e)
            }

    def process_batch(self, image_dir: str, output_dir: str, max_workers: int = 3) -> Dict:
        """批量处理图片"""
        print("🚀 开始百度OCR批量处理")
        print("=" * 60)
        print(f"📁 图片目录: {image_dir}")
        print(f"📁 输出目录: {output_dir}")
        print(f"🔄 并发数: {max_workers}")

        # 获取图片文件
        image_files = self.get_image_files(image_dir)

        if not image_files:
            print("❌ 未找到图片文件")
            return {'success': False, 'message': '未找到图片文件'}

        print(f"📊 找到 {len(image_files)} 个图片文件")

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 生成输出文件路径
        output_files = []
        for image_file in image_files:
            image_name = Path(image_file).stem
            output_file = Path(output_dir) / f"{image_name}_baidu.md"
            output_files.append(str(output_file))

        print(f"\n🔄 开始处理...")
        print("=" * 60)

        # 开始批量处理
        start_time = datetime.now()

        # 使用进度条显示处理进度
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = []
            for img_file, out_file in zip(image_files, output_files):
                future = executor.submit(self.process_single_image_safe, img_file, out_file)
                futures.append(future)

            # 处理结果并显示进度
            results = []
            for future in tqdm(concurrent.futures.as_completed(futures),
                              total=len(futures),
                              desc="百度OCR处理进度"):
                result = future.result()
                results.append(result)
                self.processed_count += 1

                # 每处理10个文件显示一次统计
                if self.processed_count % 10 == 0:
                    success_rate = (self.success_count / self.processed_count) * 100
                    print(f"\n📈 进度: {self.processed_count}/{len(image_files)} "
                          f"成功率: {success_rate:.1f}% "
                          f"({self.success_count}/{self.failed_count})")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 生成最终统计
        final_stats = {
            'total_files': len(image_files),
            'processed_files': self.processed_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'success_rate': (self.success_count / len(image_files)) * 100,
            'total_time': total_time,
            'avg_time_per_file': total_time / len(image_files) if image_files else 0,
            'results': results
        }

        print(f"\n🎉 批量处理完成!")
        print("=" * 60)
        print(f"📊 统计结果:")
        print(f"   总文件数: {final_stats['total_files']}")
        print(f"   成功: {final_stats['success_count']}")
        print(f"   失败: {final_stats['failed_count']}")
        print(f"   成功率: {final_stats['success_rate']:.1f}%")
        print(f"   总用时: {total_time:.1f}秒")
        print(f"   平均速度: {final_stats['avg_time_per_file']:.2f}秒/文件")

        return final_stats

    def generate_report(self, stats: Dict, output_dir: str):
        """生成详细报告"""
        report_file = Path(output_dir) / "baidu_ocr_batch_report.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 百度OCR批量处理报告\n\n")
            f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 总体统计
            f.write("## 总体统计\n\n")
            f.write(f"- 总文件数: {stats['total_files']}\n")
            f.write(f"- 成功处理: {stats['success_count']}\n")
            f.write(f"- 处理失败: {stats['failed_count']}\n")
            f.write(f"- 成功率: {stats['success_rate']:.1f}%\n")
            f.write(f"- 总用时: {stats['total_time']:.1f}秒\n")
            f.write(f"- 平均速度: {stats['avg_time_per_file']:.2f}秒/文件\n\n")

            # 成本估算
            cost_per_request = 0.0015  # 元
            total_cost = stats['total_files'] * cost_per_request
            f.write(f"- 成本估算: {total_cost:.2f}元\n")
            f.write(f"- 免费额度: 每日500-1000次\n\n")

            # 失败文件详情
            if stats['failed_count'] > 0:
                f.write("## 失败文件详情\n\n")
                failed_results = [r for r in stats['results'] if not r['success']]
                for i, result in enumerate(failed_results[:10], 1):  # 显示前10个失败文件
                    f.write(f"### {i}. {Path(result['image_file']).name}\n")
                    f.write(f"错误信息: {result['error']}\n")
                    f.write(f"处理时间: {result['processing_time']:.2f}秒\n\n")

                if len(failed_results) > 10:
                    f.write(f"... 还有 {len(failed_results) - 10} 个失败文件\n\n")

            # 成功文件示例
            success_results = [r for r in stats['results'] if r['success']]
            if success_results:
                f.write("## 成功文件示例\n\n")
                # 选择几个不同大小的成功文件作为示例
                small_file = min(success_results, key=lambda x: x['char_count'])
                large_file = max(success_results, key=lambda x: x['char_count'])
                avg_file = sorted(success_results, key=lambda x: x['char_count'])[len(success_results)//2]

                for example, title in [(small_file, "小文件示例"), (large_file, "大文件示例"), (avg_file, "中等文件示例")]:
                    f.write(f"### {title}\n")
                    f.write(f"文件: {Path(example['image_file']).name}\n")
                    f.write(f"字符数: {example['char_count']}\n")
                    f.write(f"单词数: {example['word_count']}\n")
                    f.write(f"处理时间: {example['processing_time']:.2f}秒\n\n")

            # 质量对比建议
            f.write("## 质量对比建议\n\n")
            f.write("为了对比百度OCR与Tesseract的效果，建议：\n\n")
            f.write("1. **随机抽样对比**: 选择10-20个不同内容的图片\n")
            f.write("2. **人工评估**: 对比两种OCR的准确性、格式保持等\n")
            f.write("3. **关注中文内容**: 重点对比中文识别效果\n")
            f.write("4. **检查表格和特殊格式**: 对比复杂布局的处理效果\n\n")

            f.write("## 后续步骤\n\n")
            f.write("1. 对比分析百度OCR与原始Tesseract结果\n")
            f.write("2. 评估质量改进效果\n")
            f.write("3. 决定是否全面采用百度OCR\n")
            f.write("4. 建立最优OCR处理策略\n\n")

            f.write("---\n")
            f.write("*报告生成时间: {}*\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        print(f"📄 详细报告已保存: {report_file}")

def main():
    """主函数"""
    print("🚀 百度OCR批量处理器")
    print("=" * 60)

    # API凭据
    api_key = "Y5iCqs919ZJP1Og1fEQqGsSW"
    secret_key = "c8La43KW46QInpCD3muLZIdtc1DiKpKa"

    # 目标目录
    image_dir = "/Users/lixiangqun/Work/AI Positioning/老板案例/案例照片2"
    output_dir = "baidu_ocr_results"

    # 初始化处理器
    processor = BaiduOCRBatchProcessor(api_key, secret_key)

    # 开始批量处理
    stats = processor.process_batch(image_dir, output_dir, max_workers=3)

    # 生成报告
    processor.generate_report(stats, output_dir)

    # 显示最终结果
    print(f"\n🎯 处理完成!")
    print(f"📁 结果保存在: {output_dir}/")
    print(f"📄 详细报告: {output_dir}/baidu_ocr_batch_report.md")

    # 提醒对比测试
    print(f"\n💡 下一步建议:")
    print(f"1. 对比百度OCR结果与原始Tesseract结果")
    print(f"2. 评估质量改进效果")
    print(f"3. 选择最优的OCR处理方案")

if __name__ == "__main__":
    main()