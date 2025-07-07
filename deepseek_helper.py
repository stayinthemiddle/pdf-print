#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek API 集成模块
提供API客户端封装、缓存、错误处理和成本追踪
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

import requests
import yaml

class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化客户端"""
        # 如果config.yaml不存在，尝试使用config_example.yaml
        if not os.path.exists(config_path) and config_path == "config.yaml":
            if os.path.exists("config_example.yaml"):
                self.logger = logging.getLogger(__name__)
                self.logger.warning("config.yaml 不存在，使用 config_example.yaml")
                config_path = "config_example.yaml"
            else:
                raise FileNotFoundError("请先复制 config_example.yaml 为 config.yaml 并配置API密钥")
        
        self.config = self._load_config(config_path)
        self.api_key = self._get_api_key()
        self.base_url = self.config['deepseek']['base_url']
        self.model = self.config['deepseek']['model']
        
        # 设置缓存
        self.cache_enabled = self.config['extraction']['cache_enabled']
        self.cache_dir = Path(self.config['extraction']['cache_dir'])
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 统计信息
        self.stats_file = self.cache_dir / "api_stats.json"
        self.stats = self._load_stats()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_api_key(self) -> str:
        """获取API密钥"""
        api_key = self.config['deepseek']['api_key']
        if not api_key:
            api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if not api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量或在 config.yaml 中配置 api_key")
        return api_key
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config['logging']
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format'],
            handlers=[
                logging.FileHandler(log_config['file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_stats(self) -> dict:
        """加载API使用统计"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            'total_calls': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'daily_calls': {},
            'monthly_cost': {}
        }
    
    def _save_stats(self):
        """保存API使用统计"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """生成缓存键"""
        cache_data = f"{prompt}{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[dict]:
        """获取缓存的响应"""
        if not self.cache_enabled:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查缓存是否过期
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            ttl = timedelta(seconds=self.config['extraction']['cache_ttl'])
            if datetime.now() - cached_time < ttl:
                self.logger.info(f"使用缓存响应: {cache_key}")
                return cache_data['response']
        
        return None
    
    def _save_to_cache(self, cache_key: str, response: dict):
        """保存响应到缓存"""
        if not self.cache_enabled:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'response': response
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    
    def _update_stats(self, tokens_used: int, cost: float):
        """更新使用统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        
        self.stats['total_calls'] += 1
        self.stats['total_tokens'] += tokens_used
        self.stats['total_cost'] += cost
        
        # 更新每日统计
        if today not in self.stats['daily_calls']:
            self.stats['daily_calls'][today] = 0
        self.stats['daily_calls'][today] += 1
        
        # 更新每月成本
        if month not in self.stats['monthly_cost']:
            self.stats['monthly_cost'][month] = 0.0
        self.stats['monthly_cost'][month] += cost
        
        self._save_stats()
        
        # 检查限制
        self._check_limits(today, month)
    
    def _check_limits(self, today: str, month: str):
        """检查API调用限制"""
        daily_limit = self.config['limits']['daily_api_calls']
        monthly_budget = self.config['limits']['monthly_budget']
        
        if self.stats['daily_calls'].get(today, 0) >= daily_limit:
            self.logger.warning(f"已达到每日API调用限制: {daily_limit}")
        
        if self.stats['monthly_cost'].get(month, 0) >= monthly_budget:
            self.logger.warning(f"已达到每月预算限制: {monthly_budget}元")
    
    def chat_completion(self, prompt: str, temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None, **kwargs) -> Optional[dict]:
        """调用DeepSeek聊天完成API"""
        # 检查缓存
        cache_key = self._get_cache_key(prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # 准备请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature or self.config['deepseek']['temperature'],
            "max_tokens": max_tokens or self.config['deepseek']['max_tokens'],
            **kwargs
        }
        
        # 重试机制
        retry_config = self.config['retry']
        for attempt in range(retry_config['max_attempts']):
            try:
                self.logger.info(f"调用DeepSeek API (尝试 {attempt + 1}/{retry_config['max_attempts']})")
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.config['deepseek']['timeout']
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 计算成本
                    usage = result.get('usage', {})
                    total_tokens = usage.get('total_tokens', 0)
                    cost = total_tokens / 1000 * self.config['limits']['cost_per_1k_tokens']
                    
                    # 更新统计
                    self._update_stats(total_tokens, cost)
                    
                    # 保存到缓存
                    self._save_to_cache(cache_key, result)
                    
                    self.logger.info(f"API调用成功，使用tokens: {total_tokens}, 成本: {cost:.4f}元")
                    return result
                
                else:
                    self.logger.error(f"API调用失败: {response.status_code} - {response.text}")
                    
                    if response.status_code == 429:  # Rate limit
                        wait_time = retry_config['initial_delay'] * (2 ** attempt if retry_config['exponential_backoff'] else 1)
                        self.logger.info(f"触发频率限制，等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                    else:
                        break
                        
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求异常: {str(e)}")
                if attempt < retry_config['max_attempts'] - 1:
                    wait_time = retry_config['initial_delay'] * (2 ** attempt if retry_config['exponential_backoff'] else 1)
                    time.sleep(wait_time)
                else:
                    raise
        
        return None
    
    def extract_json_from_response(self, response: dict) -> Optional[dict]:
        """从API响应中提取JSON数据"""
        try:
            if not response:
                return None
            
            content = response['choices'][0]['message']['content']
            
            # 尝试直接解析JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 尝试提取JSON块
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # 尝试提取花括号内的内容
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            
            self.logger.warning("无法从响应中提取JSON")
            return None
            
        except Exception as e:
            self.logger.error(f"提取JSON失败: {str(e)}")
            return None
    
    def get_stats_summary(self) -> str:
        """获取统计摘要"""
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        
        summary = f"""
DeepSeek API 使用统计
====================
总调用次数: {self.stats['total_calls']}
总使用tokens: {self.stats['total_tokens']:,}
总成本: ¥{self.stats['total_cost']:.2f}

今日调用次数: {self.stats['daily_calls'].get(today, 0)}
本月成本: ¥{self.stats['monthly_cost'].get(month, 0):.2f}

限制:
- 每日调用限制: {self.config['limits']['daily_api_calls']}
- 每月预算: ¥{self.config['limits']['monthly_budget']}
"""
        return summary
    
    def clear_cache(self):
        """清除缓存"""
        if self.cache_dir.exists():
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("缓存已清除")


def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek API 工具')
    parser.add_argument('--stats', action='store_true', help='显示API使用统计')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存')
    parser.add_argument('--test', action='store_true', help='测试API连接')
    
    args = parser.parse_args()
    
    client = DeepSeekClient()
    
    if args.stats:
        print(client.get_stats_summary())
    
    elif args.clear_cache:
        client.clear_cache()
        print("缓存已清除")
    
    elif args.test:
        print("测试DeepSeek API连接...")
        response = client.chat_completion("Hello, please respond with 'OK' if you receive this message.")
        if response:
            print("✅ API连接成功!")
            print(f"模型: {client.model}")
        else:
            print("❌ API连接失败!")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()