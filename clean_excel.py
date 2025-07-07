#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""清理Excel记录，只保留实际存在的PDF文件"""

import os
import pandas as pd
from pathlib import Path

def clean_excel_records():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chinese_dir = os.path.join(base_dir, '中文pdf')
    english_dir = os.path.join(base_dir, '英文pdf')
    excel_path = os.path.join(base_dir, 'pdf_records.xlsx')
    
    # 获取实际存在的PDF文件
    existing_files = []
    
    # 检查中文PDF
    if os.path.exists(chinese_dir):
        for f in os.listdir(chinese_dir):
            if f.endswith('.pdf'):
                existing_files.append(f)
    
    # 检查英文PDF
    if os.path.exists(english_dir):
        for f in os.listdir(english_dir):
            if f.endswith('.pdf'):
                existing_files.append(f)
    
    print(f"找到 {len(existing_files)} 个实际存在的PDF文件：")
    for f in existing_files:
        print(f"  - {f}")
    
    # 读取Excel
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path, engine='openpyxl')
        original_count = len(df)
        
        # 只保留实际存在的文件记录
        df_cleaned = df[df['文件名'].isin(existing_files)]
        cleaned_count = len(df_cleaned)
        
        # 保存清理后的Excel
        df_cleaned.to_excel(excel_path, index=False, engine='openpyxl')
        
        print(f"\n清理完成！")
        print(f"原始记录数：{original_count}")
        print(f"清理后记录数：{cleaned_count}")
        print(f"删除了 {original_count - cleaned_count} 条无效记录")
    else:
        print("\nExcel文件不存在")

if __name__ == "__main__":
    clean_excel_records()