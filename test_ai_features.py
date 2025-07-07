#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试AI功能的示例脚本
演示如何使用DeepSeek AI增强的PDF管理功能
"""

import os
import sys

def print_separator():
    print("=" * 60)

def test_api_connection():
    """测试DeepSeek API连接"""
    print("\n1. 测试DeepSeek API连接")
    print_separator()
    os.system("python deepseek_helper.py --test")
    print_separator()

def test_metadata_extraction():
    """测试AI元数据提取"""
    print("\n2. 测试AI元数据提取")
    print_separator()
    
    # 查找一个PDF文件进行测试
    test_pdf = None
    for folder in ['中文pdf', '英文pdf']:
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
            if files:
                test_pdf = os.path.join(folder, files[0])
                break
    
    if test_pdf:
        print(f"测试文件: {test_pdf}")
        print("\n传统方法提取:")
        os.system(f'python llm_extractor.py "{test_pdf}" --traditional')
        
        print("\n\nAI方法提取:")
        os.system(f'python llm_extractor.py "{test_pdf}"')
    else:
        print("未找到测试PDF文件")
    
    print_separator()

def test_batch_processing():
    """测试批量处理功能"""
    print("\n3. 测试批量处理（使用AI）")
    print_separator()
    print("运行命令: python pdf_batch_processor.py --use-ai")
    print("注意：这将处理所有新的PDF文件")
    response = input("是否继续？(y/n): ")
    
    if response.lower() == 'y':
        os.system("python pdf_batch_processor.py --use-ai")
    else:
        print("跳过批量处理测试")
    
    print_separator()

def test_paper_matching():
    """测试文献配对功能"""
    print("\n4. 测试中英文文献配对")
    print_separator()
    print("运行命令: python paper_matcher.py --no-semantic")
    print("这将基于基础特征进行快速配对分析")
    
    os.system("python paper_matcher.py --no-semantic --output test_matching.html")
    
    if os.path.exists("test_matching.html"):
        print(f"\n配对报告已生成: test_matching.html")
        print("可以在浏览器中打开查看")
    
    print_separator()

def show_api_stats():
    """显示API使用统计"""
    print("\n5. API使用统计")
    print_separator()
    os.system("python deepseek_helper.py --stats")
    print_separator()

def main():
    """主函数"""
    print("🤖 DeepSeek AI PDF管理系统测试")
    print("=" * 60)
    
    # 检查API密钥
    from deepseek_helper import DeepSeekClient
    try:
        client = DeepSeekClient()
        print("✅ API配置已就绪")
    except ValueError as e:
        print(f"❌ 错误: {e}")
        print("\n请设置环境变量:")
        print("export DEEPSEEK_API_KEY='your-api-key'")
        print("或在 config.yaml 中配置 api_key")
        return
    
    while True:
        print("\n选择测试项目:")
        print("1. 测试API连接")
        print("2. 测试AI元数据提取")
        print("3. 测试批量处理")
        print("4. 测试文献配对")
        print("5. 查看API统计")
        print("0. 退出")
        
        choice = input("\n请选择 (0-5): ")
        
        if choice == '0':
            break
        elif choice == '1':
            test_api_connection()
        elif choice == '2':
            test_metadata_extraction()
        elif choice == '3':
            test_batch_processing()
        elif choice == '4':
            test_paper_matching()
        elif choice == '5':
            show_api_stats()
        else:
            print("无效选择")
        
        input("\n按回车继续...")

if __name__ == "__main__":
    main()