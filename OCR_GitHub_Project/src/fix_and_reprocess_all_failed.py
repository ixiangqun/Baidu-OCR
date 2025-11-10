#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复并重新处理所有52个失败文件
"""

import os
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
from baidu_ocr_integration import BaiduOCRProcessor
import concurrent.futures
from tqdm import tqdm
from typing import List, Dict, Tuple

class AllFailedFilesProcessor:
    """所有失败文件处理器"""

    def __init__(self, api_key: str, secret_key: str):
        """初始化处理器"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.processor = BaiduOCRProcessor(api_key, secret_key)
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'size_fixed': 0,
            'format_fixed': 0,
            'errors': 0
        }

    def check_and_fix_image(self, image_path: str, output_path: str) -> bool:
        """检查并修复图片"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = os.path.getsize(image_path)
                format_type = img.format

                needs_fix = False
                issues = []

                # 检查百度OCR要求
                if file_size > 4 * 1024 * 1024:
                    issues.append('file_size')
                    needs_fix = True

                if width > 4096 or height > 4096:
                    issues.append('dimension')
                    needs_fix = True

                if format_type not in ['JPEG', 'PNG', 'BMP']:
                    issues.append('format')
                    needs_fix = True

                if not needs_fix:
                    # 图片符合要求，直接复制
                    import shutil
                    shutil.copy2(image_path, output_path)
                    return True, "no_fix_needed"

                print(f"🔧 修复 {Path(image_path).name}: {issues}")

                # 需要修复
                temp_img = img.copy()

                # 先调整尺寸
                if 'dimension' in issues:
                    max_size = (4096, 4096)
                    temp_img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    self.stats['size_fixed'] += 1

                # 保存为JPEG格式
                save_kwargs = {'format': 'JPEG', 'quality': 95, 'optimize': True}

                # 如果需要压缩文件大小
                if 'file_size' in issues:
                    # 逐步降低质量
                    for quality in range(95, 60, -5):
                        save_kwargs['quality'] = quality
                        temp_path = output_path + '.temp'
                        temp_img.save(temp_path, **save_kwargs)

                        if os.path.getsize(temp_path) <= 4 * 1024 * 1024:
                            os.rename(temp_path, output_path)
                            self.stats['size_fixed'] += 1
                            return True, "size_fixed"
                        else:
                            os.remove(temp_path)

                    # 如果还是太大，继续缩小尺寸
                    current_width, current_height = temp_img.size
                    while os.path.getsize(temp_path + '.temp2') > 4 * 1024 * 1024 if os.path.exists(temp_path + '.temp2') else True:
                        current_width = int(current_width * 0.9)
                        current_height = int(current_height * 0.9)
                        temp_img = temp_img.resize((current_width, current_height), Image.Resampling.LANCZOS)

                        temp_path2 = output_path + '.temp2'
                        for quality in range(95, 60, -5):
                            temp_img.save(temp_path2, format='JPEG', quality=quality, optimize=True)
                            if os.path.getsize(temp_path2) <= 4 * 1024 * 1024:
                                if os.path.exists(output_path):
                                    os.remove(output_path)
                                os.rename(temp_path2, output_path)
                                return True, "size_compressed"
                            os.remove(temp_path2)

                else:
                    # 直接保存
                    temp_img.save(output_path, **save_kwargs)
                    if 'format' in issues:
                        self.stats['format_fixed'] += 1

                return True, "fixed"

        except Exception as e:
            print(f"❌ 修复失败 {Path(image_path).name}: {e}")
            self.stats['errors'] += 1
            return False, str(e)

    def process_single_image_safe(self, image_file: str, output_file: str) -> Dict:
        """安全处理单个图片"""
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

                self.stats['success_count'] += 1
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
                self.stats['failed_count'] += 1
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
            self.stats['failed_count'] += 1
            return {
                'success': False,
                'image_file': image_file,
                'output_file': output_file,
                'processing_time': 0,
                'char_count': 0,
                'word_count': 0,
                'error': str(e)
            }

    def process_all_failed_files(self, input_dir: str, temp_dir: str, output_dir: str, max_workers: int = 3) -> Dict:
        """处理所有失败文件"""
        print("🚀 处理所有52个失败文件")
        print("=" * 60)
        print(f"📁 输入目录: {input_dir}")
        print(f"📁 临时目录: {temp_dir}")
        print(f"📁 输出目录: {output_dir}")
        print(f"🔄 并发数: {max_workers}")

        # 确保目录存在
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 获取所有失败文件
        failed_files = [
            "20151202_212224.jpg", "20151202_224237.jpg", "20151203_031846.jpg",
            "20151203_031858.jpg", "20151203_031910.jpg", "20151203_031913.jpg",
            "20151203_031924.jpg", "20151203_032047.jpg", "20151203_032447.jpg",
            "20151203_032529.jpg", "20151203_032544.jpg", "20151203_032629.jpg",
            "20151203_032651.jpg", "20151203_032723.jpg", "20151203_032819.jpg",
            "20151203_033405.jpg", "20151203_033453.jpg", "20151203_034006.jpg",
            "20151203_034053.jpg", "20151203_034626.jpg", "20151203_034656.jpg",
            "20151203_035509.jpg", "20151203_035608.jpg", "20151203_035650.jpg",
            "20151203_035953.jpg", "20151203_040023.jpg", "20151203_040108.jpg",
            "20151203_040139.jpg", "20151203_040406.jpg", "20151203_040421.jpg",
            "20151203_041158.jpg", "20151203_041231.jpg", "20151203_041259.jpg",
            "20151203_041308.jpg", "20151203_041427.jpg", "20151203_041605.jpg",
            "20151203_041732.jpg", "20151203_041858.jpg", "20151203_042024.jpg",
            "20151203_042120.jpg", "20151203_042339.jpg", "20151203_042553.jpg",
            "20151203_042601.jpg", "20151203_042634.jpg", "20151203_042746.jpg",
            "20151203_042808.jpg", "20151203_042842.jpg", "20151203_042904.jpg",
            "20151203_043025.jpg", "20151203_043041.jpg", "20151203_043425.jpg",
            "20151203_044345.jpg"
        ]

        print(f"📊 发现 {len(failed_files)} 个失败文件")

        # 第一步：检查和修复所有图片
        print(f"\n🔧 第一步：检查和修复图片...")
        print("=" * 60)

        fix_results = []
        available_files = []

        for i, filename in enumerate(failed_files, 1):
            input_path = Path(input_dir) / filename
            temp_path = Path(temp_dir) / filename

            if not input_path.exists():
                print(f"⚠️  文件不存在: {filename}")
                continue

            print(f"[{i:2d}/{len(failed_files)}] 处理: {filename}")

            # 检查并修复图片
            success, fix_type = self.check_and_fix_image(str(input_path), str(temp_path))

            if success:
                available_files.append(str(temp_path))
                fix_results.append({
                    'filename': filename,
                    'fixed': fix_type != "no_fix_needed",
                    'fix_type': fix_type
                })
                if fix_type == "no_fix_needed":
                    print(f"   ✅ 无需修复")
                else:
                    print(f"   ✅ 修复完成 ({fix_type})")
            else:
                print(f"   ❌ 修复失败")

        print(f"\n📊 修复统计:")
        print(f"   总文件: {len(failed_files)}")
        print(f"   可处理: {len(available_files)}")
        print(f"   需要修复: {sum(1 for r in fix_results if r['fixed'])}")
        print(f"   修复失败: {len(failed_files) - len(available_files)}")

        if not available_files:
            print("❌ 没有可处理的文件")
            return {'success': False, 'message': '没有可处理的文件'}

        # 第二步：重新进行OCR处理
        print(f"\n🔄 第二步：重新进行OCR处理...")
        print("=" * 60)

        # 生成输出文件路径
        output_files = []
        for image_file in available_files:
            image_name = Path(image_file).stem
            output_file = Path(output_dir) / f"{image_name}_baidu_final.md"
            output_files.append(str(output_file))

        # 开始批量处理
        start_time = datetime.now()

        # 使用进度条显示处理进度
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = []
            for img_file, out_file in zip(available_files, output_files):
                future = executor.submit(self.process_single_image_safe, img_file, out_file)
                futures.append(future)

            # 处理结果并显示进度
            results = []
            for future in tqdm(concurrent.futures.as_completed(futures),
                              total=len(futures),
                              desc="OCR处理进度"):
                result = future.result()
                results.append(result)
                self.stats['total_processed'] += 1

                # 每处理10个文件显示一次统计
                if self.stats['total_processed'] % 10 == 0:
                    success_rate = (self.stats['success_count'] / self.stats['total_processed']) * 100
                    print(f"\n📈 进度: {self.stats['total_processed']}/{len(available_files)} "
                          f"成功率: {success_rate:.1f}% "
                          f"({self.stats['success_count']}/{self.stats['failed_count']})")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 生成最终统计
        final_stats = {
            'total_files': len(failed_files),
            'available_files': len(available_files),
            'processed_files': self.stats['total_processed'],
            'success_count': self.stats['success_count'],
            'failed_count': self.stats['failed_count'],
            'success_rate': (self.stats['success_count'] / len(available_files)) * 100 if available_files else 0,
            'total_time': total_time,
            'avg_time_per_file': total_time / len(available_files) if available_files else 0,
            'fix_stats': self.stats.copy(),
            'results': results,
            'fix_results': fix_results
        }

        print(f"\n🎉 全部处理完成!")
        print("=" * 60)
        print(f"📊 最终统计:")
        print(f"   总失败文件: {final_stats['total_files']}")
        print(f"   可处理文件: {final_stats['available_files']}")
        print(f"   成功处理: {final_stats['success_count']}")
        print(f"   处理失败: {final_stats['failed_count']}")
        print(f"   成功率: {final_stats['success_rate']:.1f}%")
        print(f"   总用时: {total_time:.1f}秒")
        print(f"   平均速度: {final_stats['avg_time_per_file']:.2f}秒/文件")

        return final_stats

    def generate_final_report(self, stats: Dict, output_dir: str):
        """生成最终报告"""
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        report_file = Path(output_dir) / "final_reprocess_report.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 所有失败文件重新处理最终报告\n\n")
            f.write(f"最终处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 总体统计
            f.write("## 总体统计\n\n")
            f.write(f"- 总失败文件: {stats['total_files']}\n")
            f.write(f"- 可处理文件: {stats['available_files']}\n")
            f.write(f"- 成功处理: {stats['success_count']}\n")
            f.write(f"- 处理失败: {stats['failed_count']}\n")
            f.write(f"- 成功率: {stats['success_rate']:.1f}%\n")
            f.write(f"- 总用时: {stats['total_time']:.1f}秒\n")
            f.write(f"- 平均速度: {stats['avg_time_per_file']:.2f}秒/文件\n\n")

            # 修复统计
            f.write("## 图片修复统计\n\n")
            f.write(f"- 尺寸修复: {stats['fix_stats']['size_fixed']}\n")
            f.write(f"- 格式修复: {stats['fix_stats']['format_fixed']}\n")
            f.write(f"- 修复错误: {stats['fix_stats']['errors']}\n\n")

            # 整体改进效果
            original_total = 428
            original_success = 377
            original_rate = 87.9

            new_success = original_success + stats['success_count']
            new_rate = (new_success / original_total) * 100

            f.write("## 整体改进效果\n\n")
            f.write(f"- 原始成功率: {original_rate}% ({original_success}/{original_total})\n")
            f.write(f"- 重新处理后: {new_rate:.1f}% ({new_success}/{original_total})\n")
            f.write(f"- 成功率提升: +{new_rate - original_rate:.1f}%\n\n")

            # 成功案例展示
            if stats['success_count'] > 0:
                f.write("## 成功案例展示\n\n")
                success_results = [r for r in stats['results'] if r['success']]

                # 按字符数排序，展示最好的案例
                success_results.sort(key=lambda x: x['char_count'], reverse=True)

                for i, result in enumerate(success_results[:10], 1):
                    f.write(f"### {i}. {Path(result['image_file']).name}\n")
                    f.write(f"字符数: {result['char_count']}\n")
                    f.write(f"单词数: {result['word_count']}\n")
                    f.write(f"处理时间: {result['processing_time']:.2f}秒\n\n")

            # 结论
            f.write("## 最终结论\n\n")
            if stats['success_rate'] > 90:
                f.write("✅ **巨大成功！**\n\n")
                f.write("通过系统性的图片修复和重新处理，绝大多数失败文件都已成功识别。\n")
                f.write(f"整体成功率从{original_rate}%提升至{new_rate:.1f}%，效果显著。\n\n")
            elif stats['success_rate'] > 70:
                f.write("✅ **显著改进**\n\n")
                f.write("大部分失败文件已成功处理，整体成功率有明显提升。\n\n")
            else:
                f.write("⚠️ **部分改进**\n\n")
                f.write("有一定改进，但仍有较多文件需要进一步处理。\n\n")

            f.write("## 推荐后续操作\n\n")
            f.write("1. **整合结果**: 将重新处理的结果与原始结果合并\n")
            f.write("2. **质量检查**: 对重新处理的结果进行质量抽查\n")
            f.write("3. **建立标准**: 建立图片预处理标准流程\n")
            f.write("4. **监控成本**: 确保API使用量在免费额度内\n\n")

            f.write("---\n")
            f.write(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        print(f"📄 最终报告已保存: {report_file}")

def main():
    """主函数"""
    print("🚀 所有失败文件最终处理器")
    print("=" * 60)

    # API凭据
    api_key = "Y5iCqs919ZJP1Og1fEQqGsSW"
    secret_key = "c8La43KW46QInpCD3muLZIdtc1DiKpKa"

    # 目录设置
    input_dir = "/Users/lixiangqun/Work/AI Positioning/老板案例/案例照片2"
    temp_dir = "all_failed_temp"
    output_dir = "all_failed_results"

    # 初始化处理器
    processor = AllFailedFilesProcessor(api_key, secret_key)

    # 开始处理
    stats = processor.process_all_failed_files(input_dir, temp_dir, output_dir, max_workers=3)

    # 生成报告
    processor.generate_final_report(stats, output_dir)

    # 显示最终结果
    print(f"\n🎯 全部处理完成!")
    print(f"📁 结果保存在: {output_dir}/")
    print(f"📄 详细报告: {output_dir}/final_reprocess_report.md")

    # 计算整体改进
    original_total = 428
    original_success = 377
    original_rate = 87.9

    new_success = original_success + stats['success_count']
    new_rate = (new_success / original_total) * 100

    print(f"\n📈 整体改进:")
    print(f"   原始成功率: {original_rate}% ({original_success}/{original_total})")
    print(f"   最终成功率: {new_rate:.1f}% ({new_success}/{original_total})")
    print(f"   成功率提升: +{new_rate - original_rate:.1f}%")

    if stats['total_files'] > 0:
        recovery_rate = (stats['success_count'] / stats['total_files']) * 100
        print(f"   失败文件恢复率: {recovery_rate:.1f}% ({stats['success_count']}/{stats['total_files']})")

if __name__ == "__main__":
    main()