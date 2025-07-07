#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""重建Excel记录 - 扫描所有已存在的PDF文件"""

import os
import re
import argparse
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from pdf_batch_processor import PDFMetadataExtractor, ExcelManager

# 导入AI模块（如果可用）
try:
    from llm_extractor import LLMExtractor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

def rebuild_records(use_ai=False, batch_size=20):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chinese_dir = os.path.join(base_dir, '中文pdf')
    english_dir = os.path.join(base_dir, '英文pdf')
    excel_path = os.path.join(base_dir, 'pdf_records.xlsx')
    
    # 删除旧的Excel文件
    if os.path.exists(excel_path):
        os.remove(excel_path)
        print("已删除旧的Excel文件")
    
    # 初始化Excel管理器
    excel_manager = ExcelManager(excel_path)
    
    # 初始化提取器
    if use_ai and AI_AVAILABLE:
        llm_extractor = LLMExtractor()
        print("🤖 使用AI增强提取")
    else:
        traditional_extractor = PDFMetadataExtractor()
        if use_ai and not AI_AVAILABLE:
            print("⚠️  AI模块不可用，使用传统方法")
    
    print("\n🔄 重建PDF记录...")
    print("=" * 50)
    
    total_count = 0
    
    # 处理中文PDF
    print("\n📂 扫描中文PDF文件夹...")
    if os.path.exists(chinese_dir):
        chinese_files = [f for f in sorted(os.listdir(chinese_dir)) if f.endswith('.pdf')]
        for filename in tqdm(chinese_files, desc="处理中文PDF"):
            if filename.endswith('.pdf'):
                match = re.match(r'^c(\d+)\.pdf$', filename)
                if match:
                    file_path = os.path.join(chinese_dir, filename)
                    counter = int(match.group(1))
                    
                    # 提取元数据
                    if use_ai and AI_AVAILABLE:
                        metadata = llm_extractor.extract_metadata(file_path, use_llm=True)
                        extraction_method = 'AI'
                        confidence = metadata.get('confidence', '0')
                    else:
                        metadata = traditional_extractor.extract_metadata(file_path)
                        extraction_method = '传统'
                        confidence = '30'
                    
                    # 准备记录
                    record = {
                        '序号': counter,
                        '文件名': filename,
                        '原始文件名': '未知',  # 无法恢复原始文件名
                        '类型': '中文',
                        '标题': metadata.get('title', ''),
                        '作者': metadata.get('authors', metadata.get('author', '')),
                        '期刊': metadata.get('journal', ''),
                        '年份': metadata.get('year', ''),
                        'DOI': metadata.get('doi', ''),
                        '添加时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        '提取方式': extraction_method,
                        '提取置信度': confidence,
                        '配对文献': '',
                        '配对置信度': ''
                    }
                    
                    excel_manager.add_record(record)
                    print(f"   ✅ 添加记录: {filename}")
                    total_count += 1
    
    # 处理英文PDF
    print("\n📂 扫描英文PDF文件夹...")
    if os.path.exists(english_dir):
        english_files = [f for f in sorted(os.listdir(english_dir)) if f.endswith('.pdf')]
        for filename in tqdm(english_files, desc="处理英文PDF"):
            if filename.endswith('.pdf'):
                match = re.match(r'^e(\d+)\.pdf$', filename)
                if match:
                    file_path = os.path.join(english_dir, filename)
                    counter = int(match.group(1))
                    
                    # 提取元数据
                    if use_ai and AI_AVAILABLE:
                        metadata = llm_extractor.extract_metadata(file_path, use_llm=True)
                        extraction_method = 'AI'
                        confidence = metadata.get('confidence', '0')
                    else:
                        metadata = traditional_extractor.extract_metadata(file_path)
                        extraction_method = '传统'
                        confidence = '30'
                    
                    # 准备记录
                    record = {
                        '序号': counter,
                        '文件名': filename,
                        '原始文件名': '未知',  # 无法恢复原始文件名
                        '类型': '英文',
                        '标题': metadata['title'],
                        '作者': metadata['author'],
                        '期刊': metadata['journal'],
                        '年份': metadata['year'],
                        'DOI': metadata['doi'],
                        '添加时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    excel_manager.add_record(record)
                    print(f"   ✅ 添加记录: {filename}")
                    total_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 重建完成！共添加 {total_count} 条记录")
    print(f"📝 记录已保存到: pdf_records.xlsx")

def main():
    parser = argparse.ArgumentParser(description='重建PDF记录')
    parser.add_argument('--use-ai', action='store_true', help='使用AI提取元数据')
    parser.add_argument('--batch-size', type=int, default=20, help='批处理大小')
    
    args = parser.parse_args()
    rebuild_records(use_ai=args.use_ai, batch_size=args.batch_size)

if __name__ == "__main__":
    main()