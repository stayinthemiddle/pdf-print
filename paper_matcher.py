#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
中英文文献配对分析模块
使用DeepSeek API进行语义分析，找出可能的中英文配对
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm
from jinja2 import Template

from deepseek_helper import DeepSeekClient
from llm_extractor import LLMExtractor

# 文献配对分析 Prompt 模板
MATCH_PROMPT = """你是一个文献配对专家。请分析以下两篇论文是否为同一篇文献的中英文版本。

文献1（{lang1}）：
- 标题：{title1}
- 作者：{authors1}
- 期刊：{journal1}
- 年份：{year1}
- 关键词：{keywords1}
- DOI：{doi1}

文献2（{lang2}）：
- 标题：{title2}
- 作者：{authors2}
- 期刊：{journal2}
- 年份：{year2}
- 关键词：{keywords2}
- DOI：{doi2}

请分析并返回JSON格式的结果：
{{
  "is_same_paper": true或false,
  "confidence": 0-100的数值,
  "evidence": {{
    "title_similarity": "标题相似度说明",
    "author_match": "作者匹配情况",
    "year_match": "年份是否一致",
    "journal_match": "期刊是否相同或对应",
    "keyword_overlap": "关键词重叠情况",
    "doi_match": "DOI匹配情况"
  }},
  "conclusion": "简要说明判断理由"
}}"""

# HTML报告模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF文献配对分析报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1, h2 {
            color: #2c3e50;
        }
        .summary {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .match-pair {
            background-color: #fff;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }
        .high-confidence {
            border-left-color: #27ae60;
        }
        .medium-confidence {
            border-left-color: #f39c12;
        }
        .low-confidence {
            border-left-color: #e74c3c;
        }
        .paper-info {
            margin: 10px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        .confidence-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }
        .confidence-high {
            background-color: #27ae60;
        }
        .confidence-medium {
            background-color: #f39c12;
        }
        .confidence-low {
            background-color: #e74c3c;
        }
        .evidence {
            margin-top: 15px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 4px;
        }
        .evidence h4 {
            margin-top: 0;
            color: #34495e;
        }
        .evidence ul {
            margin: 5px 0;
            padding-left: 20px;
        }
        .timestamp {
            text-align: right;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>📚 PDF文献配对分析报告</h1>
    
    <div class="summary">
        <h2>📊 分析摘要</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_chinese }}</div>
                <div class="stat-label">中文文献</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_english }}</div>
                <div class="stat-label">英文文献</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ high_confidence_matches }}</div>
                <div class="stat-label">高置信度配对</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_matches }}</div>
                <div class="stat-label">总配对数</div>
            </div>
        </div>
    </div>
    
    <h2>🔍 配对结果</h2>
    
    {% for match in matches %}
    <div class="match-pair {% if match.confidence >= 80 %}high-confidence{% elif match.confidence >= 60 %}medium-confidence{% else %}low-confidence{% endif %}">
        <h3>配对 #{{ loop.index }}</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="paper-info">
                <strong>🇨🇳 中文文献 ({{ match.chinese_file }})</strong>
                <p><strong>标题:</strong> {{ match.chinese_title }}</p>
                <p><strong>作者:</strong> {{ match.chinese_authors }}</p>
                <p><strong>期刊:</strong> {{ match.chinese_journal }}</p>
                <p><strong>年份:</strong> {{ match.chinese_year }}</p>
            </div>
            
            <div class="paper-info">
                <strong>🇬🇧 英文文献 ({{ match.english_file }})</strong>
                <p><strong>标题:</strong> {{ match.english_title }}</p>
                <p><strong>作者:</strong> {{ match.english_authors }}</p>
                <p><strong>期刊:</strong> {{ match.english_journal }}</p>
                <p><strong>年份:</strong> {{ match.english_year }}</p>
            </div>
        </div>
        
        <div style="margin-top: 15px;">
            <span class="confidence-badge {% if match.confidence >= 80 %}confidence-high{% elif match.confidence >= 60 %}confidence-medium{% else %}confidence-low{% endif %}">
                置信度: {{ match.confidence }}%
            </span>
        </div>
        
        <div class="evidence">
            <h4>匹配证据</h4>
            <ul>
                {% for key, value in match.evidence.items() %}
                <li><strong>{{ key }}:</strong> {{ value }}</li>
                {% endfor %}
            </ul>
            <p><strong>结论:</strong> {{ match.conclusion }}</p>
        </div>
    </div>
    {% endfor %}
    
    <div class="timestamp">
        生成时间: {{ timestamp }}
    </div>
</body>
</html>
"""

class PaperMatcher:
    """文献配对分析器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化配对分析器"""
        self.client = DeepSeekClient(config_path)
        self.extractor = LLMExtractor(config_path)
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = self.client.config
        self.threshold = self.config['matching']['similarity_threshold']
        self.batch_size = self.config['matching']['batch_size']
        
        # 设置路径
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.chinese_dir = self.base_dir / '中文pdf'
        self.english_dir = self.base_dir / '英文pdf'
        self.excel_path = self.base_dir / 'pdf_records.xlsx'
    
    def load_paper_metadata(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """从Excel加载论文元数据"""
        try:
            df = pd.read_excel(self.excel_path, engine='openpyxl')
            
            # 分离中英文论文
            chinese_df = df[df['类型'] == '中文'].copy()
            english_df = df[df['类型'] == '英文'].copy()
            
            self.logger.info(f"加载元数据: {len(chinese_df)}篇中文, {len(english_df)}篇英文")
            return chinese_df, english_df
            
        except Exception as e:
            self.logger.error(f"加载Excel失败: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()
    
    def calculate_basic_similarity(self, paper1: pd.Series, paper2: pd.Series) -> float:
        """计算两篇论文的基础相似度"""
        similarity_scores = []
        
        # 年份匹配
        if paper1['年份'] and paper2['年份']:
            year_sim = 1.0 if paper1['年份'] == paper2['年份'] else 0.0
            similarity_scores.append(year_sim * 0.3)  # 年份权重30%
        
        # DOI匹配
        if paper1['DOI'] and paper2['DOI']:
            doi_sim = 1.0 if paper1['DOI'] == paper2['DOI'] else 0.0
            similarity_scores.append(doi_sim * 0.4)  # DOI权重40%
        
        # 标题长度相似度（粗略估计）
        if paper1['标题'] and paper2['标题']:
            len_ratio = min(len(paper1['标题']), len(paper2['标题'])) / max(len(paper1['标题']), len(paper2['标题']))
            similarity_scores.append(len_ratio * 0.1)  # 长度权重10%
        
        # 作者数量相似度
        if paper1['作者'] and paper2['作者']:
            authors1 = len(paper1['作者'].split(';'))
            authors2 = len(paper2['作者'].split(';'))
            if authors1 > 0 and authors2 > 0:
                author_ratio = min(authors1, authors2) / max(authors1, authors2)
                similarity_scores.append(author_ratio * 0.2)  # 作者权重20%
        
        return sum(similarity_scores) if similarity_scores else 0.0
    
    def analyze_paper_pair(self, chinese_paper: pd.Series, english_paper: pd.Series) -> Optional[Dict]:
        """使用LLM分析一对论文是否匹配"""
        try:
            # 构建prompt
            prompt = MATCH_PROMPT.format(
                lang1="中文",
                title1=chinese_paper['标题'] or '未知',
                authors1=chinese_paper['作者'] or '未知',
                journal1=chinese_paper['期刊'] or '未知',
                year1=chinese_paper['年份'] or '未知',
                keywords1=chinese_paper.get('关键词', '') or '未知',
                doi1=chinese_paper['DOI'] or '无',
                lang2="英文",
                title2=english_paper['标题'] or '未知',
                authors2=english_paper['作者'] or '未知',
                journal2=english_paper['期刊'] or '未知',
                year2=english_paper['年份'] or '未知',
                keywords2=english_paper.get('关键词', '') or '未知',
                doi2=english_paper['DOI'] or '无'
            )
            
            # 调用API
            response = self.client.chat_completion(prompt)
            if not response:
                return None
            
            # 提取结果
            result = self.client.extract_json_from_response(response)
            if not result:
                return None
            
            # 添加文件信息
            result['chinese_file'] = chinese_paper['文件名']
            result['english_file'] = english_paper['文件名']
            result['chinese_title'] = chinese_paper['标题']
            result['english_title'] = english_paper['标题']
            result['chinese_authors'] = chinese_paper['作者']
            result['english_authors'] = english_paper['作者']
            result['chinese_journal'] = chinese_paper['期刊']
            result['english_journal'] = english_paper['期刊']
            result['chinese_year'] = chinese_paper['年份']
            result['english_year'] = english_paper['年份']
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析配对失败: {str(e)}")
            return None
    
    def find_all_matches(self, use_semantic: bool = True) -> List[Dict]:
        """查找所有可能的配对"""
        # 加载数据
        chinese_df, english_df = self.load_paper_metadata()
        if chinese_df.empty or english_df.empty:
            self.logger.warning("没有足够的数据进行配对分析")
            return []
        
        matches = []
        
        # 首先进行基础筛选
        potential_pairs = []
        for _, c_paper in chinese_df.iterrows():
            for _, e_paper in english_df.iterrows():
                basic_sim = self.calculate_basic_similarity(c_paper, e_paper)
                if basic_sim > 0.3:  # 基础相似度阈值
                    potential_pairs.append((c_paper, e_paper, basic_sim))
        
        # 按相似度排序
        potential_pairs.sort(key=lambda x: x[2], reverse=True)
        
        self.logger.info(f"找到 {len(potential_pairs)} 个潜在配对")
        
        # 使用语义分析进一步验证
        if use_semantic and self.config['matching']['use_semantic_analysis']:
            # 批量处理
            for i in tqdm(range(0, len(potential_pairs), self.batch_size), desc="分析配对"):
                batch = potential_pairs[i:i + self.batch_size]
                
                for c_paper, e_paper, basic_sim in batch:
                    result = self.analyze_paper_pair(c_paper, e_paper)
                    if result and result.get('is_same_paper'):
                        matches.append(result)
        else:
            # 只使用基础相似度
            for c_paper, e_paper, basic_sim in potential_pairs:
                if basic_sim >= self.threshold:
                    matches.append({
                        'chinese_file': c_paper['文件名'],
                        'english_file': e_paper['文件名'],
                        'chinese_title': c_paper['标题'],
                        'english_title': e_paper['标题'],
                        'chinese_authors': c_paper['作者'],
                        'english_authors': e_paper['作者'],
                        'chinese_journal': c_paper['期刊'],
                        'english_journal': e_paper['期刊'],
                        'chinese_year': c_paper['年份'],
                        'english_year': e_paper['年份'],
                        'confidence': int(basic_sim * 100),
                        'is_same_paper': True,
                        'evidence': {
                            '基础相似度': f"{basic_sim:.2f}"
                        },
                        'conclusion': '基于基础特征匹配'
                    })
        
        # 按置信度排序
        matches.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return matches
    
    def generate_html_report(self, matches: List[Dict], output_path: str = "matching_report.html"):
        """生成HTML格式的配对报告"""
        # 统计信息
        chinese_df, english_df = self.load_paper_metadata()
        
        stats = {
            'total_chinese': len(chinese_df),
            'total_english': len(english_df),
            'total_matches': len(matches),
            'high_confidence_matches': sum(1 for m in matches if m.get('confidence', 0) >= 80),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matches': matches
        }
        
        # 渲染HTML
        template = Template(HTML_TEMPLATE)
        html_content = template.render(**stats)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"报告已生成: {output_path}")
        return output_path
    
    def update_excel_with_matches(self, matches: List[Dict]):
        """更新Excel文件，添加配对信息"""
        try:
            # 读取现有Excel
            df = pd.read_excel(self.excel_path, engine='openpyxl')
            
            # 添加新列（如果不存在）
            if '配对文献' not in df.columns:
                df['配对文献'] = ''
            if '配对置信度' not in df.columns:
                df['配对置信度'] = ''
            
            # 更新配对信息
            for match in matches:
                # 只更新英文文献（记录对应的中文版）
                mask = df['文件名'] == match['english_file']
                df.loc[mask, '配对文献'] = match['chinese_file']
                df.loc[mask, '配对置信度'] = match.get('confidence', '')
                
                # 中文文献的配对信息保持为空
                mask = df['文件名'] == match['chinese_file']
                df.loc[mask, '配对文献'] = ''
                df.loc[mask, '配对置信度'] = ''
            
            # 保存更新
            df.to_excel(self.excel_path, index=False, engine='openpyxl')
            self.logger.info("Excel文件已更新配对信息")
            
        except Exception as e:
            self.logger.error(f"更新Excel失败: {str(e)}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF文献配对分析工具')
    parser.add_argument('--output', default='matching_report.html', help='输出报告文件名')
    parser.add_argument('--no-semantic', action='store_true', help='不使用语义分析')
    parser.add_argument('--update-excel', action='store_true', help='更新Excel文件')
    parser.add_argument('--threshold', type=float, help='相似度阈值')
    
    args = parser.parse_args()
    
    matcher = PaperMatcher()
    
    # 设置阈值
    if args.threshold:
        matcher.threshold = args.threshold
    
    print("🔍 开始分析文献配对...")
    matches = matcher.find_all_matches(use_semantic=not args.no_semantic)
    
    print(f"\n✅ 找到 {len(matches)} 个配对")
    
    # 生成报告
    report_path = matcher.generate_html_report(matches, args.output)
    print(f"📊 报告已生成: {report_path}")
    
    # 更新Excel
    if args.update_excel and matches:
        matcher.update_excel_with_matches(matches)
        print("📝 Excel文件已更新")


if __name__ == "__main__":
    main()