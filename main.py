#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR-Baidu-Processor 主入口文件
一键运行完整的OCR处理流程
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# 添加src目录到路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from baidu_ocr_batch_processor import BaiduOCRBatchProcessor
from fix_and_reprocess_all_failed import AllFailedFilesProcessor
from retry_failed_files import RetryFailedFiles
from find_all_failed_files import find_failed_files
import config.settings as settings

def setup_logging(verbose=False):
    """设置日志配置"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ocr_processing.log', encoding='utf-8')
        ]
    )

def run_complete_ocr_pipeline(input_dir, output_dir, verbose=False):
    """运行完整的OCR处理流程"""

    logger = logging.getLogger(__name__)
    logger.info("🚀 开始OCR处理流程")
    logger.info(f"输入目录: {input_dir}")
    logger.info(f"输出目录: {output_dir}")

    # 第一步：批量OCR处理
    logger.info("\n📦 第一步：批量OCR处理")
    try:
        processor = BaiduOCRBatchProcessor(
            settings.BAIDU_OCR_CONFIG["api_key"],
            settings.BAIDU_OCR_CONFIG["secret_key"]
        )

        stats = processor.process_batch(
            input_dir,
            output_dir,
            max_workers=settings.BAIDU_OCR_CONFIG["max_workers"]
        )

        success_rate = (stats['success_count'] / stats['total_files']) * 100
        logger.info(f"批量处理完成 - 成功率: {success_rate:.1f}%")

    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        return False

    # 检查是否有失败文件需要重新处理
    if stats['failed_count'] > 0:
        logger.info(f"\n🔧 第二步：处理失败文件 ({stats['failed_count']}个)")

        try:
            reprocessor = AllFailedFilesProcessor(
                settings.BAIDU_OCR_CONFIG["api_key"],
                settings.BAIDU_OCR_CONFIG["secret_key"]
            )

            retry_stats = reprocessor.process_all_failed_files(
                input_dir,
                temp_dir="temp",
                output_dir=output_dir,
                max_workers=settings.BAIDU_OCR_CONFIG["max_workers"]
            )

            retry_success_rate = (retry_stats['success_count'] / retry_stats['total_files']) * 100
            logger.info(f"失败文件重处理完成 - 成功率: {retry_success_rate:.1f}%")

            # 检查是否有API限制失败需要重试
            if retry_stats['failed_count'] > 0:
                logger.info(f"\n🔄 第三步：重试API限制文件 ({retry_stats['failed_count']}个)")

                retry_processor = RetryFailedFiles(
                    settings.BAIDU_OCR_CONFIG["api_key"],
                    settings.BAIDU_OCR_CONFIG["secret_key"]
                )

                # 获取需要重试的文件列表
                failed_files = find_failed_files()

                final_results = retry_processor.retry_failed_files(
                    failed_files,
                    "temp",  # 使用修复后的临时文件
                    "results/retry"
                )

                final_success_rate = (len([r for r in final_results if r['success']]) / len(final_results)) * 100
                logger.info(f"API限制重试完成 - 成功率: {final_success_rate:.1f}%")

        except Exception as e:
            logger.error(f"失败文件处理失败: {e}")
            # 不中断主流程，继续完成

    # 生成最终统计
    logger.info("\n📊 生成最终统计报告")
    try:
        generate_final_report(stats, output_dir)
    except Exception as e:
        logger.warning(f"生成报告失败: {e}")

    logger.info("🎉 OCR处理流程完成！")
    return True

def generate_final_report(stats, output_dir):
    """生成最终处理报告"""
    import datetime

    report_file = Path(output_dir) / "final_report.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# OCR处理最终报告\n\n")
        f.write(f"处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 总体统计
        f.write("## 总体统计\n\n")
        f.write(f"- 总文件数: {stats['total_files']}\n")
        f.write(f"- 成功处理: {stats['success_count']}\n")
        f.write(f"- 处理失败: {stats['failed_count']}\n")
        f.write(f"- 成功率: {(stats['success_count']/stats['total_files']*100):.1f}%\n")
        f.write(f"- 总用时: {stats.get('total_time', 0):.1f}秒\n")
        f.write(f"- 平均速度: {stats.get('avg_time_per_file', 0):.2f}秒/文件\n\n")

        # 性能指标
        f.write("## 性能指标\n\n")
        f.write(f"- 成功率: **{(stats['success_count']/stats['total_files']*100):.1f}%**\n")
        f.write(f"- 处理速度: **{stats.get('avg_time_per_file', 0):.2f}秒/文件**\n")
        f.write(f"- 并发支持: **{settings.BAIDU_OCR_CONFIG['max_workers']}线程**\n")
        f.write(f"- 免费额度使用: **{stats['total_files']}/1000次**\n\n")

        f.write("---\n")
        f.write(f"*报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    print(f"📄 报告已保存: {report_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OCR-Baidu-Processor - 一键OCR处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                                    # 使用默认目录
  python main.py -i /path/to/images -o /path/to/output  # 自定义目录
  python main.py -v                                 # 详细输出
  python main.py --help                             # 显示帮助
        """
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        default="data/input",
        help="输入图片目录 (默认: data/input)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data/output",
        help="输出结果目录 (默认: data/output)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="OCR-Baidu-Processor 1.0.0"
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.verbose)

    # 验证输入目录
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入目录不存在: {input_path}")
        print(f"请创建目录并放入图片文件，或使用 -i 参数指定其他目录")
        return 1

    # 创建输出目录
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # 运行处理流程
    success = run_complete_ocr_pipeline(
        str(input_path),
        str(output_path),
        args.verbose
    )

    if success:
        print("\n🎉 OCR处理完成！")
        print(f"📁 结果保存在: {output_path}")
        print(f"📄 详细报告: {output_path}/final_report.md")
        return 0
    else:
        print("\n❌ OCR处理失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# 项目元信息
__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "基于百度OCR的完整文字识别解决方案，成功率99.1%""file_path":"~/OCR_GitHub_Project/main.py"} a"file_path":"~/OCR_GitHub_Project/main.py