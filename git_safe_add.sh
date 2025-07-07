#!/bin/bash

echo "🔒 安全添加文件到Git"
echo "======================"

# 首先确保.gitignore生效
echo "1. 添加.gitignore..."
git add .gitignore

# 添加文档文件
echo -e "\n2. 添加文档文件..."
git add README.md

# 添加示例配置（不是实际配置）
echo -e "\n3. 添加示例配置..."
git add config_example.yaml

# 添加依赖文件
echo -e "\n4. 添加依赖文件..."
git add requirements.txt

# 添加所有Python脚本
echo -e "\n5. 添加Python脚本..."
git add pdf_batch_processor.py
git add pdf_manager.py
git add deepseek_helper.py
git add llm_extractor.py
git add paper_matcher.py
git add enhanced_matcher.py
git add clean_excel.py
git add fix_metadata.py
git add process_existing.py
git add rebuild_records.py
git add setup_ai.py
git add test_ai_features.py

# 添加模板文件
echo -e "\n6. 添加HTML模板..."
git add enhanced_report_template.html

# 添加Shell脚本
echo -e "\n7. 添加Shell脚本..."
git add git_safe_add.sh

# 显示将要提交的文件
echo -e "\n✅ 以下文件已添加到暂存区："
git status --short | grep "^A"

# 显示被忽略的文件
echo -e "\n🚫 以下敏感文件被忽略（不会上传）："
echo "- config.yaml (包含API密钥)"
echo "- *.log (日志文件)"
echo "- .cache/ (缓存目录)"
echo "- pdf_records.xlsx (你的数据)"
echo "- config.yaml.backup (配置备份)"
echo "- enhanced_matching_report.html (生成的报告)"
echo "- matching_report.html (生成的报告)"
echo "- 中文pdf/ (PDF文件夹)"
echo "- 英文pdf/ (PDF文件夹)"

# 检查是否有config.yaml在追踪中
if git ls-files | grep -q "config.yaml"; then
    echo -e "\n⚠️  警告：config.yaml 已经被Git追踪！"
    echo "运行以下命令移除追踪："
    echo "git rm --cached config.yaml"
fi

echo -e "\n下一步："
echo "1. 检查状态: git status"
echo "2. 提交更改: git commit -m '添加AI功能支持'"
echo "3. 推送代码: git push"