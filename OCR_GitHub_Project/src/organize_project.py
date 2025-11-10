#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR项目整理工具
整理现有的OCR处理工具和文件到标准项目结构
"""

import os
import shutil
from pathlib import Path

def organize_project():
    """整理OCR项目到标准结构"""

    # 定义项目根目录
    project_root = Path.home() / "OCR_Project"

    # 定义源文件位置（当前目录）
    current_dir = Path.cwd()

    # OCR工具文件列表
    ocr_tools = [
        "baidu_ocr_integration.py",
        "baidu_ocr_batch_processor.py",
        "fix_and_reprocess_all_failed.py",
        "retry_failed_files.py",
        "find_all_failed_files.py",
        "analyze_ocr_failures.py",
        "fix_ocr_images.py",
        "test_fixed_images.py",
        "extract_failed_files.py"
    ]

    # 报告文件列表
    report_files = [
        "final_complete_summary.md",
        "final_ocr_results_summary.md"
    ]

    # 结果文件模式
    result_patterns = [
        "*_baidu.md",
        "*_baidu_final.md",
        "*_baidu_retry.md",
        "*report.md"
    ]

    print("🧹 OCR项目整理工具")
    print("=" * 50)
    print(f"项目根目录: {project_root}")
    print(f"当前目录: {current_dir}")

    # 1. 整理工具文件
    print("\n📦 整理工具文件...")
    tools_moved = 0
    for tool_file in ocr_tools:
        src_file = current_dir / tool_file
        dst_file = project_root / "tools" / tool_file

        if src_file.exists():
            try:
                shutil.copy2(src_file, dst_file)
                print(f"✅ {tool_file}")
                tools_moved += 1
            except Exception as e:
                print(f"❌ {tool_file}: {e}")
        else:
            print(f"⚠️  {tool_file} 不存在")

    # 2. 整理报告文件
    print(f"\n📊 整理报告文件...")
    reports_moved = 0
    for report_file in report_files:
        src_file = current_dir / report_file
        dst_file = project_root / "reports" / report_file

        if src_file.exists():
            try:
                shutil.copy2(src_file, dst_file)
                print(f"✅ {report_file}")
                reports_moved += 1
            except Exception as e:
                print(f"❌ {report_file}: {e}")

    # 3. 整理结果文件
    print(f"\n📝 整理结果文件...")
    results_moved = 0

    # 查找所有结果文件
    for pattern in result_patterns:
        for src_file in current_dir.glob(pattern):
            if src_file.is_file():
                dst_file = project_root / "results" / "baidu_ocr" / src_file.name
                try:
                    shutil.copy2(src_file, dst_file)
                    print(f"✅ {src_file.name}")
                    results_moved += 1
                except Exception as e:
                    print(f"❌ {src_file.name}: {e}")

    # 4. 移动现有结果目录
    print(f"\n📁 移动现有结果目录...")

    existing_result_dirs = [
        ("baidu_ocr_results", "baidu_ocr"),
        ("all_failed_results", "failed_reprocess"),
        ("retry_results", "retry")
    ]

    dirs_moved = 0
    for src_dir_name, dst_dir_name in existing_result_dirs:
        src_dir = current_dir / src_dir_name
        dst_dir = project_root / "results" / dst_dir_name

        if src_dir.exists() and src_dir.is_dir():
            try:
                # 复制目录内容
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
                print(f"✅ {src_dir_name} -> {dst_dir_name}")
                dirs_moved += 1
            except Exception as e:
                print(f"❌ {src_dir_name}: {e}")

    # 5. 创建配置文件模板
    print(f"\n⚙️ 创建配置文件...")
    config_file = project_root / "config" / "settings.py"

    config_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR项目配置文件
"""

# 百度OCR API配置
BAIDU_OCR_CONFIG = {
    "api_key": "Y5iCqs919ZJP1Og1fEQqGsSW",
    "secret_key": "c8La43KW46QInpCD3muLZIdtc1DiKpKa",
    "max_workers": 3,  # 并发处理数
    "retry_delay": 2,  # 重试延迟基数
    "max_retries": 3,  # 最大重试次数
}

# 路径配置
PATHS = {
    "original_images": "~/OCR_Project/original_images",
    "results": "~/OCR_Project/results",
    "reports": "~/OCR_Project/reports",
    "temp": "~/OCR_Project/temp"
}

# 图片处理参数
IMAGE_SETTINGS = {
    "max_size_mb": 4,  # 最大文件大小(MB)
    "max_dimension": 4096,  # 最大尺寸(像素)
    "quality": 95,  # JPEG质量
    "supported_formats": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
}
'''

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ 创建配置文件")
    except Exception as e:
        print(f"❌ 配置文件创建失败: {e}")

    # 6. 创建主处理脚本
    print(f"\n🎯 创建主处理脚本...")
    main_script = project_root / "run_ocr_pipeline.py"

    main_script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR处理主流程脚本
一键运行完整的OCR处理流程
"""

import os
import sys
from pathlib import Path

def run_ocr_pipeline():
    """运行完整的OCR处理流程"""

    project_root = Path(__file__).parent
    tools_dir = project_root / "tools"

    print("🚀 OCR处理主流程")
    print("=" * 50)
    print(f"项目目录: {project_root}")

    # 第一步：批量处理
    print("\\n📦 第一步：批量处理图片...")
    os.chdir(tools_dir)
    result1 = os.system("python baidu_ocr_batch_processor.py")

    if result1 != 0:
        print("❌ 批量处理失败")
        return False

    # 第二步：处理失败文件
    print("\\n🔧 第二步：处理失败文件...")
    result2 = os.system("python fix_and_reprocess_all_failed.py")

    if result2 != 0:
        print("❌ 失败文件处理失败")
        return False

    # 第三步：重试API限制文件（如需要）
    print("\\n🔄 第三步：重试API限制文件...")
    result3 = os.system("python retry_failed_files.py")

    if result3 != 0:
        print("⚠️  重试处理失败（可选步骤）")

    print("\\n🎉 OCR处理流程完成！")
    print("请查看 results 目录获取处理结果")
    print("请查看 reports 目录获取详细报告")

    return True

if __name__ == "__main__":
    success = run_ocr_pipeline()
    sys.exit(0 if success else 1)
'''

    try:
        with open(main_script, 'w', encoding='utf-8') as f:
            f.write(main_script_content)

        # 添加执行权限
        os.chmod(main_script, 0o755)
        print(f"✅ 创建主处理脚本")
    except Exception as e:
        print(f"❌ 主脚本创建失败: {e}")

    # 总结报告
    print(f"\\n" + "=" * 50)
    print("📊 整理完成统计")
    print("=" * 50)
    print(f"✅ 工具文件: {tools_moved} 个")
    print(f"✅ 报告文件: {reports_moved} 个")
    print(f"✅ 结果文件: {results_moved} 个")
    print(f"✅ 结果目录: {dirs_moved} 个")
    print(f"✅ 配置文件: 1 个")
    print(f"✅ 主脚本: 1 个")
    print(f"\\n🎯 项目已整理完成！")
    print(f"📁 项目位置: {project_root}")
    print(f"\\n下一步操作:")
    print(f"1. 将您的图片文件放入: {project_root}/original_images/")
    print(f"2. 运行: cd {project_root} && python run_ocr_pipeline.py")
    print(f"3. 查看结果: {project_root}/results/")
    print(f"4. 查看报告: {project_root}/reports/")

if __name__ == "__main__":
    organize_project()