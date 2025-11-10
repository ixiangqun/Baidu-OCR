#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度AI Studio OCR 集成模块
提供更强大的OCR识别能力，特别针对中文和复杂布局优化
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time

class BaiduOCRClient:
    """百度OCR客户端"""

    def __init__(self, api_key: str, secret_key: str, app_id: str = None):
        """
        初始化百度OCR客户端

        Args:
            api_key: API Key
            secret_key: Secret Key
            app_id: App ID（可选）
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.app_id = app_id
        self.access_token = None
        self.token_expires = 0
        self.base_url = "https://aip.baidubce.com/rest/2.0/ocr/v1"

        # 获取访问令牌
        self._get_access_token()

    def _get_access_token(self):
        """获取访问令牌"""
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.secret_key
        }

        try:
            response = requests.post(token_url, params=params)
            result = response.json()

            if 'access_token' in result:
                self.access_token = result['access_token']
                self.token_expires = time.time() + result.get('expires_in', 3600) - 300  # 提前5分钟过期
                print("✅ 百度OCR令牌获取成功")
            else:
                raise Exception(f"获取令牌失败: {result}")

        except Exception as e:
            print(f"❌ 获取令牌失败: {e}")
            raise

    def _ensure_token_valid(self):
        """确保令牌有效"""
        if not self.access_token or time.time() > self.token_expires:
            self._get_access_token()

    def _make_request(self, endpoint: str, image_data: bytes, params: Dict = None) -> Dict:
        """发送API请求"""
        self._ensure_token_valid()

        url = f"{self.base_url}/{endpoint}?access_token={self.access_token}"

        # 构建请求数据
        data = {
            'image': base64.b64encode(image_data).decode('utf-8')
        }

        if params:
            data.update(params)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(url, data=data, headers=headers)
            result = response.json()

            if 'error_code' in result:
                raise Exception(f"API错误: {result.get('error_msg', 'Unknown error')}")

            return result

        except Exception as e:
            print(f"❌ API请求失败: {e}")
            raise

    def general_text_ocr(self, image_path: str, **kwargs) -> Dict:
        """
        通用文字识别

        Args:
            image_path: 图片路径
            **kwargs: 其他参数
                - language_type: 语言类型 (CHN_ENG/ENG/JAP/KOR...)
                - detect_direction: 是否检测朝向 (true/false)
                - detect_language: 是否检测语言 (true/false)
                - probability: 是否返回置信度 (true/false)

        Returns:
            OCR结果字典
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()

        return self._make_request('general', image_data, kwargs)

    def accurate_text_ocr(self, image_path: str, **kwargs) -> Dict:
        """
        通用文字识别（高精度版）

        Args:
            image_path: 图片路径
            **kwargs: 其他参数

        Returns:
            OCR结果字典
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()

        return self._make_request('general_basic', image_data, kwargs)

    def table_ocr(self, image_path: str, **kwargs) -> Dict:
        """
        表格文字识别

        Args:
            image_path: 图片路径
            **kwargs: 其他参数
                - is_sync: 是否同步返回 (true/false)
                - request_type: 请求类型 (json/excel/markdown)

        Returns:
            表格OCR结果
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # 默认返回JSON格式，包含表格结构
        params = {
            'is_sync': 'true',
            'request_type': kwargs.get('request_type', 'json')
        }
        params.update(kwargs)

        return self._make_request('form', image_data, params)

    def handwriting_ocr(self, image_path: str, **kwargs) -> Dict:
        """
        手写文字识别

        Args:
            image_path: 图片路径
            **kwargs: 其他参数

        Returns:
            手写OCR结果
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()

        return self._make_request('handwriting', image_data, kwargs)

    def multi_language_ocr(self, image_path: str, **kwargs) -> Dict:
        """
        多语言识别（支持中英文混合）

        Args:
            image_path: 图片路径
            **kwargs: 其他参数

        Returns:
            多语言OCR结果
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # 默认中英文混合
        params = {
            'language_type': kwargs.get('language_type', 'CHN_ENG')
        }
        params.update(kwargs)

        return self._make_request('general', image_data, params)

    def convert_to_markdown(self, ocr_result: Dict) -> str:
        """
        将OCR结果转换为Markdown格式

        Args:
            ocr_result: OCR结果字典

        Returns:
            Markdown格式文本
        """
        if 'words_result' not in ocr_result:
            return ""

        lines = []
        current_line = ""
        last_y = None

        # 按位置组织文本
        for word_info in ocr_result['words_result']:
            word = word_info.get('words', '')
            location = word_info.get('location', {})
            y = location.get('top', 0)

            # 简单的换行判断（基于垂直位置）
            if last_y is not None and abs(y - last_y) > 20:
                if current_line.strip():
                    lines.append(current_line.strip())
                current_line = word
            else:
                current_line += " " + word

            last_y = y

        if current_line.strip():
            lines.append(current_line.strip())

        return '\n'.join(lines)

    def convert_table_to_markdown(self, table_result: Dict) -> str:
        """
        将表格OCR结果转换为Markdown表格

        Args:
            table_result: 表格OCR结果

        Returns:
            Markdown表格格式
        """
        if 'form_result' not in table_result:
            return self.convert_to_markdown(table_result)

        form_result = table_result['form_result']
        if not form_result:
            return ""

        # 提取表格数据
        table_data = []
        for row in form_result:
            if 'row' in row:
                table_data.append(row['row'])

        if not table_data:
            return ""

        # 转换为Markdown表格
        md_lines = []

        # 表头
        if len(table_data) > 0:
            headers = table_data[0]
            md_lines.append('| ' + ' | '.join(headers) + ' |')
            md_lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')

        # 数据行
        for row in table_data[1:]:
            md_lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(md_lines)

class BaiduOCRProcessor:
    """百度OCR处理器 - 用于批量处理"""

    def __init__(self, api_key: str, secret_key: str):
        """初始化处理器"""
        self.client = BaiduOCRClient(api_key, secret_key)
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0

    def process_single_image(self, image_path: str, output_path: str, ocr_type: str = 'accurate') -> bool:
        """
        处理单张图片

        Args:
            image_path: 输入图片路径
            output_path: 输出Markdown文件路径
            ocr_type: OCR类型 ('general', 'accurate', 'table', 'handwriting')

        Returns:
            是否成功
        """
        try:
            print(f"🔄 处理: {Path(image_path).name}")

            # 根据类型选择OCR方法
            if ocr_type == 'table':
                result = self.client.table_ocr(image_path, request_type='markdown')
                content = self.client.convert_table_to_markdown(result)
            elif ocr_type == 'handwriting':
                result = self.client.handwriting_ocr(image_path)
                content = self.client.convert_to_markdown(result)
            elif ocr_type == 'accurate':
                result = self.client.accurate_text_ocr(image_path, detect_direction='true')
                content = self.client.convert_to_markdown(result)
            else:  # general
                result = self.client.general_text_ocr(image_path, detect_direction='true')
                content = self.client.convert_to_markdown(result)

            if content.strip():
                # 添加元数据
                header = f"# OCR识别结果\n\n"
                header += f"*OCR识别时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
                header += f"*OCR引擎: 百度AI Studio ({ocr_type})*\n\n"
                header += "---\n\n"

                full_content = header + content

                # 保存到文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)

                print(f"✅ 成功: {output_path}")
                self.success_count += 1
                return True
            else:
                print(f"⚠️  无内容: {image_path}")
                self.failed_count += 1
                return False

        except Exception as e:
            print(f"❌ 失败: {image_path} - {e}")
            self.failed_count += 1
            return False

        finally:
            self.processed_count += 1

    def process_batch(self, image_dir: str, output_dir: str, ocr_type: str = 'accurate',
                     extensions: List[str] = None) -> Dict[str, bool]:
        """
        批量处理图片

        Args:
            image_dir: 图片目录
            output_dir: 输出目录
            ocr_type: OCR类型
            extensions: 支持的文件扩展名

        Returns:
            处理结果字典
        """
        if extensions is None:
            extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

        image_path = Path(image_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 查找所有图片文件
        image_files = []
        for ext in extensions:
            image_files.extend(image_path.glob(f"*{ext}"))
            image_files.extend(image_path.glob(f"*{ext.upper()}"))

        image_files = sorted(list(set(image_files)))

        print(f"🚀 开始批量处理 - 百度OCR ({ocr_type})")
        print(f"📁 输入目录: {image_dir}")
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 找到 {len(image_files)} 个图片文件")

        results = {}
        start_time = datetime.now()

        for i, image_file in enumerate(image_files, 1):
            output_file = output_path / f"{image_file.stem}_baidu.md"
            success = self.process_single_image(str(image_file), str(output_file), ocr_type)
            results[str(image_file)] = success

            if i % 10 == 0:
                print(f"📈 进度: {i}/{len(image_files)}")

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        print(f"\n✅ 批量处理完成!")
        print(f"📊 统计:")
        print(f"  总文件数: {self.processed_count}")
        print(f"  成功: {self.success_count}")
        print(f"  失败: {self.failed_count}")
        print(f"  成功率: {self.success_count/self.processed_count*100:.1f}%")
        print(f"  总用时: {processing_time:.1f}秒")

        return results

def main():
    """测试函数"""
    # 这里填入你的百度AI凭据
    API_KEY = "Y5iCqs919ZJP1Og1fEQqGsSW"
    SECRET_KEY = "c8La43KW46QInpCD3muLZIdtc1DiKpKa"

    if API_KEY == "YOUR_API_KEY" or API_KEY == "":  # 检查是否已配置
        print("⚠️ 请先设置百度AI凭据")
        print("1. 访问 https://console.bce.baidu.com/ai/")
        print("2. 创建应用获取 API Key 和 Secret Key")
        print("3. 替换 main() 函数中的凭据")
        return

    processor = BaiduOCRProcessor(API_KEY, SECRET_KEY)

    # 测试单张图片
    test_image = "ocr_test_images/meeting_notes.png"
    output_file = "baidu_test_result.md"

    if os.path.exists(test_image):
        success = processor.process_single_image(test_image, output_file, 'accurate')
        if success:
            print(f"\n✅ 测试完成，结果保存在: {output_file}")
            print("📋 内容预览:")
            with open(output_file, 'r', encoding='utf-8') as f:
                print(f.read()[:500] + "..." if len(f.read()) > 500 else f.read())
        else:
            print("❌ 测试失败")
    else:
        print("⚠️ 测试图片不存在")

if __name__ == "__main__":
    main()