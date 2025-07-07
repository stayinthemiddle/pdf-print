#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI增强的PDF元数据提取模块
使用DeepSeek API智能提取文献信息
"""

import re
import logging
from typing import Dict, Optional, List
from pathlib import Path

import PyPDF2
import pdfplumber
from deepseek_helper import DeepSeekClient

# 文献信息提取 Prompt 模板
EXTRACT_PROMPT = """你是一个学术文献信息提取专家。请从以下PDF文本中准确提取文献信息。

PDF文本内容（前{pages}页）：
---
{text}
---

请提取并返回以下JSON格式的信息：
{{
  "title": "论文的完整标题",
  "title_en": "英文标题（如果是中文论文且有英文标题）",
  "authors": "所有作者姓名，用分号分隔",
  "journal": "期刊或会议名称",
  "year": "发表年份（YYYY格式）",
  "doi": "DOI号（如果存在）",
  "keywords": "关键词，用分号分隔",
  "abstract": "摘要的前100字",
  "confidence": "提取的整体置信度（0-100）"
}}

注意：
1. 如果某项信息不存在，使用空字符串""
2. 作者姓名保持原文格式
3. 年份必须是4位数字
4. DOI保持完整格式（10.xxxx/xxxxx）
5. 置信度反映你对提取结果准确性的评估"""

class LLMExtractor:
    """使用LLM的PDF元数据提取器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化提取器"""
        self.client = DeepSeekClient(config_path)
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = self.client.config
        self.max_pages = self.config['extraction']['max_pages']
        self.max_chars = self.config['extraction']['max_chars']
    
    def extract_text_from_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> str:
        """从PDF提取文本内容"""
        if max_pages is None:
            max_pages = self.max_pages
        
        text_content = []
        
        try:
            # 首先尝试使用pdfplumber（对中文支持更好）
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages[:max_pages]):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"[第{i+1}页]\n{page_text}")
                        
                        # 检查字符数限制
                        current_length = sum(len(t) for t in text_content)
                        if current_length > self.max_chars:
                            # 截断到最大字符数
                            combined = "\n\n".join(text_content)
                            return combined[:self.max_chars] + "..."
            
            # 如果pdfplumber提取失败或内容太少，尝试PyPDF2
            if len("\n\n".join(text_content)) < 100:
                self.logger.info("pdfplumber提取内容不足，尝试PyPDF2")
                text_content = []
                
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for i in range(min(max_pages, len(reader.pages))):
                        page = reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"[第{i+1}页]\n{page_text}")
                            
                            # 检查字符数限制
                            current_length = sum(len(t) for t in text_content)
                            if current_length > self.max_chars:
                                combined = "\n\n".join(text_content)
                                return combined[:self.max_chars] + "..."
            
        except Exception as e:
            self.logger.error(f"提取PDF文本失败: {str(e)}")
            return ""
        
        return "\n\n".join(text_content)
    
    def extract_metadata_traditional(self, pdf_path: str) -> Dict[str, str]:
        """传统方法提取元数据（作为备份）"""
        metadata = {
            'title': '',
            'title_en': '',
            'authors': '',
            'journal': '',
            'year': '',
            'doi': '',
            'keywords': '',
            'abstract': '',
            'confidence': '30'  # 传统方法置信度较低
        }
        
        try:
            # 使用PyPDF2提取基本元数据
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                info = reader.metadata
                
                if info:
                    metadata['title'] = info.get('/Title', '') or ''
                    metadata['authors'] = info.get('/Author', '') or ''
                    
                    # 尝试提取年份
                    creation_date = info.get('/CreationDate', '')
                    if creation_date:
                        year_match = re.search(r'(\d{4})', str(creation_date))
                        if year_match:
                            metadata['year'] = year_match.group(1)
            
            # 使用pdfplumber提取文本中的信息
            with pdfplumber.open(pdf_path) as pdf:
                # 只检查前两页
                for i, page in enumerate(pdf.pages[:2]):
                    text = page.extract_text() or ''
                    
                    # 提取DOI
                    doi_patterns = [
                        r'(?:DOI|doi)[\s:]*([^\s]+)',
                        r'10\.\d{4,}/[-._;()/:\w]+',
                    ]
                    for pattern in doi_patterns:
                        doi_match = re.search(pattern, text)
                        if doi_match:
                            metadata['doi'] = doi_match.group(1) if '10.' not in pattern else doi_match.group(0)
                            break
                    
                    # 尝试提取标题（如果为空）
                    if not metadata['title'] and i == 0:
                        lines = text.split('\n')
                        for line in lines[:10]:
                            line = line.strip()
                            # 标题通常较长且不以数字开头
                            if len(line) > 20 and not re.match(r'^\d', line):
                                metadata['title'] = line
                                break
                    
                    # 尝试提取期刊信息
                    if not metadata['journal']:
                        journal_patterns = [
                            r'(?:Journal of|IEEE|Nature|Science|Cell|Proceedings of)[^,\n]+',
                            r'(?:International|American|European|Asian) Journal of[^,\n]+',
                            r'《([^》]+)》',  # 中文期刊
                        ]
                        for pattern in journal_patterns:
                            journal_match = re.search(pattern, text, re.IGNORECASE)
                            if journal_match:
                                metadata['journal'] = journal_match.group(0).strip()
                                break
                    
                    # 提取关键词
                    if not metadata['keywords']:
                        keywords_patterns = [
                            r'(?:Keywords|关键词)[：:]\s*([^\n]+)',
                            r'(?:Key words)[：:]\s*([^\n]+)',
                        ]
                        for pattern in keywords_patterns:
                            keywords_match = re.search(pattern, text, re.IGNORECASE)
                            if keywords_match:
                                metadata['keywords'] = keywords_match.group(1).strip()
                                break
        
        except Exception as e:
            self.logger.error(f"传统方法提取元数据失败: {str(e)}")
        
        return metadata
    
    def extract_metadata_with_llm(self, pdf_path: str) -> Dict[str, str]:
        """使用LLM提取元数据"""
        try:
            # 提取PDF文本
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                self.logger.warning(f"无法从PDF提取文本: {pdf_path}")
                return self.extract_metadata_traditional(pdf_path)
            
            # 构建prompt
            prompt = EXTRACT_PROMPT.format(
                pages=self.max_pages,
                text=text
            )
            
            # 调用DeepSeek API
            self.logger.info(f"调用DeepSeek API提取元数据: {Path(pdf_path).name}")
            response = self.client.chat_completion(prompt)
            
            if not response:
                self.logger.warning("LLM API调用失败，回退到传统方法")
                return self.extract_metadata_traditional(pdf_path)
            
            # 提取JSON响应
            metadata = self.client.extract_json_from_response(response)
            
            if not metadata:
                self.logger.warning("无法解析LLM响应，回退到传统方法")
                return self.extract_metadata_traditional(pdf_path)
            
            # 验证和清理数据
            metadata = self._validate_metadata(metadata)
            
            self.logger.info(f"LLM提取成功，置信度: {metadata.get('confidence', 'N/A')}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"LLM提取元数据失败: {str(e)}")
            return self.extract_metadata_traditional(pdf_path)
    
    def _validate_metadata(self, metadata: Dict[str, str]) -> Dict[str, str]:
        """验证和清理元数据"""
        # 确保所有必需字段存在
        required_fields = ['title', 'title_en', 'authors', 'journal', 'year', 'doi', 'keywords', 'abstract', 'confidence']
        for field in required_fields:
            if field not in metadata:
                metadata[field] = ''
        
        # 验证年份格式
        if metadata['year']:
            year_match = re.search(r'(\d{4})', metadata['year'])
            if year_match:
                metadata['year'] = year_match.group(1)
            else:
                metadata['year'] = ''
        
        # 验证DOI格式
        if metadata['doi']:
            # 清理DOI（去除多余的前缀等）
            doi_match = re.search(r'10\.\d{4,}/[-._;()/:\w]+', metadata['doi'])
            if doi_match:
                metadata['doi'] = doi_match.group(0)
        
        # 确保置信度是数字
        try:
            confidence = int(metadata.get('confidence', 0))
            metadata['confidence'] = str(max(0, min(100, confidence)))
        except:
            metadata['confidence'] = '50'
        
        # 截断过长的摘要
        if len(metadata.get('abstract', '')) > 200:
            metadata['abstract'] = metadata['abstract'][:197] + '...'
        
        return metadata
    
    def extract_metadata(self, pdf_path: str, use_llm: bool = True) -> Dict[str, str]:
        """提取PDF元数据的主方法"""
        if use_llm:
            return self.extract_metadata_with_llm(pdf_path)
        else:
            return self.extract_metadata_traditional(pdf_path)


def main():
    """测试脚本"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF元数据提取工具')
    parser.add_argument('pdf_file', help='PDF文件路径')
    parser.add_argument('--traditional', action='store_true', help='只使用传统方法')
    parser.add_argument('--show-text', action='store_true', help='显示提取的文本')
    
    args = parser.parse_args()
    
    extractor = LLMExtractor()
    
    if args.show_text:
        text = extractor.extract_text_from_pdf(args.pdf_file)
        print("提取的文本内容:")
        print("=" * 50)
        print(text)
        print("=" * 50)
    
    print(f"\n提取元数据: {args.pdf_file}")
    metadata = extractor.extract_metadata(args.pdf_file, use_llm=not args.traditional)
    
    print("\n提取结果:")
    print("-" * 50)
    for key, value in metadata.items():
        if value:
            print(f"{key}: {value}")
    print("-" * 50)


if __name__ == "__main__":
    main()