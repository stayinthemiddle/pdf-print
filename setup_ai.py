#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI功能设置脚本
帮助用户配置DeepSeek API
"""

import os
import shutil
import sys

def setup_config():
    """设置配置文件"""
    print("🔧 PDF管理系统 - AI功能设置")
    print("=" * 50)
    
    # 检查是否已有config.yaml
    if os.path.exists("config.yaml"):
        print("✅ 检测到现有的 config.yaml 文件")
        response = input("是否要重新配置？(y/n): ")
        if response.lower() != 'y':
            print("保留现有配置")
            return
    
    # 复制示例文件
    if not os.path.exists("config_example.yaml"):
        print("❌ 错误：找不到 config_example.yaml 文件")
        return
    
    shutil.copy("config_example.yaml", "config.yaml")
    print("✅ 已创建 config.yaml 文件")
    
    # 询问API密钥配置方式
    print("\n请选择API密钥配置方式：")
    print("1. 使用环境变量（推荐，更安全）")
    print("2. 直接写入配置文件")
    print("3. 稍后手动配置")
    
    choice = input("\n请选择 (1-3): ")
    
    if choice == '1':
        print("\n请将以下命令添加到你的 shell 配置文件（如 ~/.zshrc 或 ~/.bashrc）：")
        print("\nexport DEEPSEEK_API_KEY='your-api-key-here'")
        print("\n然后运行 source ~/.zshrc (或对应的配置文件) 使其生效")
        
    elif choice == '2':
        api_key = input("\n请输入你的 DeepSeek API 密钥: ")
        if api_key:
            # 更新配置文件
            with open("config.yaml", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换api_key行
            import re
            content = re.sub(
                r'api_key:\s*"".*',
                f'api_key: "{api_key}"  # 已配置',
                content
            )
            
            with open("config.yaml", 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ API密钥已保存到 config.yaml")
            print("⚠️  注意：config.yaml 已在 .gitignore 中，不会被提交到版本控制")
    
    else:
        print("\n稍后配置步骤：")
        print("1. 编辑 config.yaml 文件")
        print("2. 将 api_key 字段设置为你的 DeepSeek API 密钥")
        print("或者设置环境变量 DEEPSEEK_API_KEY")
    
    print("\n✅ 设置完成！")
    print("\n下一步：")
    print("1. 安装依赖：pip install -r requirements.txt")
    print("2. 测试AI功能：python test_ai_features.py")

def check_dependencies():
    """检查依赖是否已安装"""
    print("\n检查依赖...")
    
    required_packages = [
        'requests',
        'yaml',
        'tqdm',
        'jinja2',
        'numpy',
        'pandas',
        'openpyxl'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  缺少以下依赖包：{', '.join(missing)}")
        print("请运行：pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有依赖已安装")
        return True

def test_api():
    """测试API连接"""
    try:
        from deepseek_helper import DeepSeekClient
        print("\n测试API连接...")
        client = DeepSeekClient()
        
        # 测试连接
        response = client.chat_completion("Hi, respond with 'OK' if you receive this.")
        if response:
            print("✅ API连接成功！")
            return True
        else:
            print("❌ API连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{str(e)}")
        return False

def main():
    """主函数"""
    setup_config()
    
    if check_dependencies():
        response = input("\n是否测试API连接？(y/n): ")
        if response.lower() == 'y':
            test_api()

if __name__ == "__main__":
    main()