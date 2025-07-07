# PDF文件管理系统

一个批量处理PDF文件的管理系统，可以自动重命名PDF文件、提取元数据并记录到Excel。支持DeepSeek AI增强的智能元数据提取和中英文文献配对分析。

## 功能特点

### 基础功能
- 📁 批量处理两个文件夹中的PDF：`中文pdf` 和 `英文pdf`
- 🔄 自动重命名：
  - 中文PDF: c01.pdf, c02.pdf, c03.pdf...
  - 英文PDF: e01.pdf, e02.pdf, e03.pdf...
- 📊 自动提取PDF元数据（标题、作者、期刊、年份、DOI）
- 📝 将所有信息记录到Excel文件
- 🔍 保留原始文件名记录
- 📋 生成详细的操作日志
- 🛠️ Excel记录管理工具（重建/清理）

### AI增强功能（新）
- 🤖 使用DeepSeek AI智能提取文献元数据
- 🔬 更准确的标题、作者、期刊信息识别
- 🌐 支持中英文文献智能配对分析
- 📈 提供提取置信度评分
- 💾 API调用缓存，避免重复请求
- 📊 成本追踪和使用统计

## 安装

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 配置DeepSeek API（可选，用于AI功能）：

首先复制配置文件示例：
```bash
cp config_example.yaml config.yaml
```

然后选择以下方式之一配置API密钥：

```bash
# 方法1：设置环境变量（推荐）
export DEEPSEEK_API_KEY="your-api-key"

# 方法2：编辑 config.yaml
# 将 api_key 字段设置为你的API密钥
# 注意：config.yaml 已在 .gitignore 中，不会被提交到版本控制
```

## 使用方法

### 基本使用：批量处理

#### 传统方式（快速）
```bash
python3 pdf_batch_processor.py
```

#### 使用AI增强（更准确）
```bash
python3 pdf_batch_processor.py --use-ai
```

使用步骤：
1. 将PDF文件拖入对应文件夹：
   - 中文PDF → `中文pdf/` 文件夹
   - 英文PDF → `英文pdf/` 文件夹
2. 运行上述命令，程序会自动：
   - 重命名文件（中文: c01.pdf, c02.pdf...; 英文: e01.pdf, e02.pdf...）
   - 提取PDF元数据
   - 记录到Excel文件 `pdf_records.xlsx`

### Excel记录管理

1. **重建所有记录**：
```bash
# 传统方式
python3 rebuild_records.py

# 使用AI重建（更准确）
python3 rebuild_records.py --use-ai
```

2. **清理无效记录**：
```bash
python3 clean_excel.py
```

### AI特色功能

1. **中英文文献配对分析**：
```bash
# 生成配对分析报告
python3 paper_matcher.py

# 更新Excel中的配对信息
python3 paper_matcher.py --update-excel
```

2. **查看API使用统计**：
```bash
python3 deepseek_helper.py --stats
```

3. **测试AI功能**：
```bash
python3 test_ai_features.py
```


## Excel记录内容

Excel文件包含以下列：
- 序号
- 文件名（新）
- 原始文件名
- 类型（中文/英文）
- 标题
- 作者
- 期刊
- 年份
- DOI
- 添加时间
- 提取方式（传统/AI）
- 提取置信度
- 配对文献
- 配对置信度

## 日志

- 基础运行日志：`pdf_batch.log`
- AI API调用日志：`deepseek_api.log`

## 注意事项

### 安全配置
1. **保护API密钥**：
   - `config.yaml` 已在 `.gitignore` 中，不会被提交
   - 推荐使用环境变量存储API密钥
   - 永远不要将包含API密钥的文件提交到版本控制

2. **首次使用**：
   ```bash
   # 运行设置脚本
   python3 setup_ai.py
   
   # 或手动复制配置
   cp config_example.yaml config.yaml
   # 然后编辑 config.yaml 添加API密钥
   ```

### 运行限制
1. **API配额管理**：
   - 每日API调用限制：1000次（可在config.yaml中调整）
   - 每月预算限制：10元人民币
   - 使用缓存避免重复调用

2. **性能优化**：
   - AI提取比传统方法慢，但更准确
   - 建议批量处理时使用 `--batch-size` 参数控制并发
   - 缓存有效期为24小时

3. **成本控制**：
   - 每次API调用约消耗0.001元（1000 tokens）
   - 使用 `--stats` 查看累计成本

