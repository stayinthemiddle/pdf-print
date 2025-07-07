#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动修正元数据
用于修正自动提取中的错误
"""

import pandas as pd
import argparse

def fix_metadata():
    """修正元数据"""
    parser = argparse.ArgumentParser(description='修正PDF元数据')
    parser.add_argument('--file', required=True, help='要修正的文件名（如c01.pdf）')
    parser.add_argument('--year', help='修正年份')
    parser.add_argument('--title', help='修正标题')
    parser.add_argument('--authors', help='修正作者')
    parser.add_argument('--journal', help='修正期刊')
    parser.add_argument('--doi', help='修正DOI')
    parser.add_argument('--show', action='store_true', help='只显示当前信息')
    
    args = parser.parse_args()
    
    # 读取Excel
    df = pd.read_excel('pdf_records.xlsx')
    
    # 找到对应的记录
    mask = df['文件名'] == args.file
    if not df[mask].empty:
        if args.show:
            # 显示当前信息
            record = df[mask].iloc[0]
            print(f"\n当前信息 - {args.file}:")
            print(f"标题: {record['标题']}")
            print(f"作者: {record['作者']}")
            print(f"期刊: {record['期刊']}")
            print(f"年份: {record['年份']}")
            print(f"DOI: {record['DOI']}")
            return
        
        # 修正信息
        updated = False
        if args.year:
            df.loc[mask, '年份'] = args.year
            print(f"✅ 年份已更新为: {args.year}")
            updated = True
        
        if args.title:
            df.loc[mask, '标题'] = args.title
            print(f"✅ 标题已更新")
            updated = True
        
        if args.authors:
            df.loc[mask, '作者'] = args.authors
            print(f"✅ 作者已更新")
            updated = True
        
        if args.journal:
            df.loc[mask, '期刊'] = args.journal
            print(f"✅ 期刊已更新")
            updated = True
        
        if args.doi:
            df.loc[mask, 'DOI'] = args.doi
            print(f"✅ DOI已更新为: {args.doi}")
            updated = True
        
        if updated:
            # 保存更新
            df.to_excel('pdf_records.xlsx', index=False, engine='openpyxl')
            print("\n📝 Excel文件已保存")
        else:
            print("⚠️  没有指定要更新的字段")
    else:
        print(f"❌ 未找到文件: {args.file}")
        print("\n可用的文件:")
        for f in df['文件名'].unique():
            print(f"  - {f}")

if __name__ == "__main__":
    fix_metadata()