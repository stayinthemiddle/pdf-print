#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""处理已存在的PDF文件"""

import os
import sys
from pdf_manager import PDFHandler, ExcelManager, PDFMetadataExtractor

def process_existing_files():
    """处理文件夹中已存在的PDF文件"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chinese_dir = os.path.join(base_dir, '中文pdf')
    english_dir = os.path.join(base_dir, '英文pdf')
    excel_path = os.path.join(base_dir, 'pdf_records.xlsx')
    
    # 初始化Excel管理器
    excel_manager = ExcelManager(excel_path)
    
    # 初始化处理器
    watch_dirs = {
        '中文pdf': chinese_dir,
        '英文pdf': english_dir
    }
    handler = PDFHandler(watch_dirs, excel_manager)
    
    processed = 0
    
    # 处理中文PDF
    print("📂 检查中文PDF文件夹...")
    if os.path.exists(chinese_dir):
        for filename in os.listdir(chinese_dir):
            if filename.lower().endswith('.pdf') and not filename.startswith('c'):
                file_path = os.path.join(chinese_dir, filename)
                print(f"  处理: {filename}")
                handler.process_pdf(file_path)
                processed += 1
    
    # 处理英文PDF
    print("\n📂 检查英文PDF文件夹...")
    if os.path.exists(english_dir):
        for filename in os.listdir(english_dir):
            if filename.lower().endswith('.pdf') and not filename.startswith('e'):
                file_path = os.path.join(english_dir, filename)
                print(f"  处理: {filename}")
                handler.process_pdf(file_path)
                processed += 1
    
    print(f"\n✅ 处理完成！共处理 {processed} 个文件。")
    
    if processed == 0:
        print("💡 提示：没有需要处理的文件。")
        print("   - 中文PDF应放在 '中文pdf' 文件夹")
        print("   - 英文PDF应放在 '英文pdf' 文件夹")
        print("   - 已经命名为 c01.pdf 或 e01.pdf 格式的文件会被跳过")

if __name__ == "__main__":
    process_existing_files()