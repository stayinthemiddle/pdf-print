#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的中英文文献配对分析
使用标题翻译和智能匹配算法
"""

import re
import pandas as pd
from typing import Dict, Tuple, List
from deepseek_helper import DeepSeekClient
from paper_matcher import PaperMatcher
import logging

# 翻译Prompt
TRANSLATE_PROMPT = """请将以下中文学术论文标题翻译成英文。只返回翻译结果，不要添加任何解释。

中文标题：{title}

英文翻译："""

# 增强的配对分析Prompt
ENHANCED_MATCH_PROMPT = """你是一个文献配对专家。请分析以下两篇论文是否为同一篇文献的中英文版本。

注意：中文版可能是英文版的翻译，因此：
- 年份应该相同（个人翻译不会改变发表年份）
- DOI可能不同（翻译版可能没有DOI或有不同的DOI）
- 作者姓名可能有不同的表示方式

文献1（中文）：
- 标题：{title1}
- 作者：{authors1}
- 年份：{year1}
- DOI：{doi1}
- 文本片段：{text1}

文献2（英文）：
- 标题：{title2}
- 作者：{authors2}
- 年份：{year2}
- DOI：{doi2}
- 文本片段：{text2}

请仔细分析并返回JSON格式的结果：
{{
  "is_same_paper": true或false,
  "confidence": 0-100的数值,
  "evidence": {{
    "title_match": "标题是否匹配（考虑翻译）",
    "author_match": "作者是否一致",
    "content_match": "内容是否相似",
    "year_explanation": "年份是否相同或差异的原因",
    "doi_explanation": "DOI差异的解释"
  }},
  "conclusion": "判断理由"
}}"""

class EnhancedMatcher:
    """增强的文献配对器"""
    
    def __init__(self):
        self.client = DeepSeekClient()
        self.logger = logging.getLogger(__name__)
        
    def translate_title(self, chinese_title: str) -> str:
        """将中文标题翻译成英文"""
        try:
            prompt = TRANSLATE_PROMPT.format(title=chinese_title)
            response = self.client.chat_completion(prompt)
            
            if response:
                translated = response['choices'][0]['message']['content'].strip()
                self.logger.info(f"翻译结果: {chinese_title} -> {translated}")
                return translated
            
        except Exception as e:
            self.logger.error(f"翻译失败: {str(e)}")
        
        return ""
    
    def extract_author_names(self, authors_str: str) -> List[str]:
        """提取作者姓名（处理不同格式）"""
        if not authors_str:
            return []
        
        # 分割作者
        authors = re.split(r'[;,，；]', authors_str)
        
        # 清理和标准化
        cleaned = []
        for author in authors:
            author = author.strip()
            if author:
                # 移除数字上标等
                author = re.sub(r'\d+', '', author)
                # 移除多余空格
                author = ' '.join(author.split())
                if author:
                    cleaned.append(author)
        
        return cleaned
    
    def calculate_author_similarity(self, authors1: str, authors2: str) -> float:
        """计算作者相似度"""
        list1 = self.extract_author_names(authors1)
        list2 = self.extract_author_names(authors2)
        
        if not list1 or not list2:
            return 0.0
        
        # 检查主要作者（第一作者和通讯作者）
        matches = 0
        
        # 第一作者
        if list1 and list2:
            first1 = list1[0].lower()
            first2 = list2[0].lower()
            
            # 检查是否包含相同的姓氏
            parts1 = first1.split()
            parts2 = first2.split()
            
            for p1 in parts1:
                for p2 in parts2:
                    if len(p1) > 2 and len(p2) > 2 and (p1 in p2 or p2 in p1):
                        matches += 1
                        break
        
        # 计算整体匹配率
        total_authors = max(len(list1), len(list2))
        return min(1.0, matches / max(1, total_authors // 2))
    
    def enhanced_match(self, chinese_paper: pd.Series, english_paper: pd.Series, 
                      chinese_text: str = "", english_text: str = "") -> Dict:
        """使用增强算法匹配文献"""
        try:
            # 翻译中文标题
            translated_title = self.translate_title(chinese_paper['标题'])
            
            # 快速相似度检查
            quick_score = 0
            
            # 标题相似度（考虑翻译）
            if translated_title and english_paper['标题']:
                # 简单的关键词匹配
                chinese_keywords = set(translated_title.lower().split())
                english_keywords = set(english_paper['标题'].lower().split())
                
                # 去除常见词
                stopwords = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'for', 'to', 'with'}
                chinese_keywords -= stopwords
                english_keywords -= stopwords
                
                if chinese_keywords and english_keywords:
                    overlap = len(chinese_keywords & english_keywords)
                    total = len(chinese_keywords | english_keywords)
                    title_sim = overlap / total if total > 0 else 0
                    quick_score += title_sim * 0.5
            
            # 作者相似度
            author_sim = self.calculate_author_similarity(
                chinese_paper.get('作者', ''),
                english_paper.get('作者', '')
            )
            quick_score += author_sim * 0.3
            
            # 年份相似度（个人翻译应该年份相同）
            try:
                year1 = int(chinese_paper.get('年份', 0))
                year2 = int(english_paper.get('年份', 0))
                if year1 and year2:
                    year_diff = abs(year1 - year2)
                    if year_diff == 0:
                        quick_score += 0.2  # 年份相同，加分
                    elif year_diff <= 1:
                        quick_score += 0.05  # 允许1年差异（可能是提取错误）
                    # 大于1年差异不加分
            except:
                pass
            
            # 如果快速得分太低，跳过详细分析
            if quick_score < 0.3:
                return {
                    'is_same_paper': False,
                    'confidence': int(quick_score * 100),
                    'evidence': {
                        'title_match': f"标题相似度低: {title_sim:.2f}" if 'title_sim' in locals() else "标题不匹配",
                        'author_match': f"作者相似度: {author_sim:.2f}",
                    },
                    'conclusion': '基础特征不匹配'
                }
            
            # 使用AI进行深度分析
            prompt = ENHANCED_MATCH_PROMPT.format(
                title1=chinese_paper['标题'],
                authors1=chinese_paper.get('作者', '未知'),
                year1=chinese_paper.get('年份', '未知'),
                doi1=chinese_paper.get('DOI', '无'),
                text1=chinese_text[:500] if chinese_text else '无',
                title2=english_paper['标题'],
                authors2=english_paper.get('作者', '未知'),
                year2=english_paper.get('年份', '未知'),
                doi2=english_paper.get('DOI', '无'),
                text2=english_text[:500] if english_text else '无'
            )
            
            response = self.client.chat_completion(prompt)
            if response:
                result = self.client.extract_json_from_response(response)
                if result:
                    # 添加翻译信息
                    result['translated_title'] = translated_title
                    result['quick_score'] = quick_score
                    return result
            
            # 如果AI分析失败，返回基础结果
            return {
                'is_same_paper': quick_score > 0.5,
                'confidence': int(quick_score * 100),
                'evidence': {
                    'title_match': f"翻译后标题: {translated_title}",
                    'author_match': f"作者相似度: {author_sim:.2f}",
                    'quick_score': f"快速评分: {quick_score:.2f}"
                },
                'conclusion': '基于快速评分判断'
            }
            
        except Exception as e:
            self.logger.error(f"增强匹配失败: {str(e)}")
            return None


def main():
    """主函数"""
    import argparse
    from llm_extractor import LLMExtractor
    
    parser = argparse.ArgumentParser(description='增强的文献配对分析')
    parser.add_argument('--update-excel', action='store_true', help='更新Excel文件')
    parser.add_argument('--show-details', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    # 初始化
    matcher = EnhancedMatcher()
    extractor = LLMExtractor()
    
    # 加载Excel数据
    df = pd.read_excel('pdf_records.xlsx')
    chinese_papers = df[df['类型'] == '中文']
    english_papers = df[df['类型'] == '英文']
    
    print("🔍 增强的文献配对分析")
    print("=" * 50)
    
    matches = []
    
    for _, c_paper in chinese_papers.iterrows():
        chinese_text = extractor.extract_text_from_pdf(f"中文pdf/{c_paper['文件名']}", max_pages=1)
        
        for _, e_paper in english_papers.iterrows():
            english_text = extractor.extract_text_from_pdf(f"英文pdf/{e_paper['文件名']}", max_pages=1)
            
            print(f"\n分析: {c_paper['文件名']} <-> {e_paper['文件名']}")
            
            result = matcher.enhanced_match(c_paper, e_paper, chinese_text, english_text)
            
            if result and result.get('is_same_paper'):
                matches.append({
                    'chinese_file': c_paper['文件名'],
                    'english_file': e_paper['文件名'],
                    'chinese_title': c_paper['标题'],
                    'english_title': e_paper['标题'],
                    'chinese_authors': c_paper.get('作者', ''),
                    'english_authors': e_paper.get('作者', ''),
                    'chinese_journal': c_paper.get('期刊', ''),
                    'english_journal': e_paper.get('期刊', ''),
                    'chinese_year': c_paper.get('年份', ''),
                    'english_year': e_paper.get('年份', ''),
                    'confidence': result.get('confidence', 0),
                    'evidence': result.get('evidence', {}),
                    'conclusion': result.get('conclusion', ''),
                    'translated_title': result.get('translated_title', '')
                })
                
                print(f"✅ 匹配成功！置信度: {result.get('confidence')}%")
                
                if args.show_details:
                    print(f"翻译标题: {result.get('translated_title', '')}")
                    print(f"证据: {result.get('evidence', {})}")
            else:
                print(f"❌ 不匹配")
    
    print(f"\n\n总结: 找到 {len(matches)} 个配对")
    
    # 更新Excel
    if args.update_excel and matches:
        from paper_matcher import PaperMatcher
        pm = PaperMatcher()
        pm.update_excel_with_matches(matches)
        print("✅ Excel已更新")
    
    # 生成报告
    if matches:
        # 使用增强的报告模板
        from jinja2 import Template
        from datetime import datetime
        
        # 读取模板
        with open('enhanced_report_template.html', 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        # 准备数据
        template_data = {
            'total_chinese': len(chinese_papers),
            'total_english': len(english_papers),
            'total_matches': len(matches),
            'high_confidence_matches': sum(1 for m in matches if m.get('confidence', 0) >= 80),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matches': matches
        }
        
        # 渲染模板
        template = Template(template_str)
        html_content = template.render(**template_data)
        
        # 保存报告
        with open("enhanced_matching_report.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("📊 报告已生成: enhanced_matching_report.html")


if __name__ == "__main__":
    main()