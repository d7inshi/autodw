import openai
from typing import Dict, Any

class LLMConnector:
    def __init__(self, 
                 api_key: str,
                 model: str = "gpt-4-turbo",
                 temperature: float = 0.3,
                 max_tokens: int = 1500):
        self.config = {
            "api_key": api_key,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def query(self, prompt: str) -> str:
        """使用MCP技术执行多轮一致性查询"""
        responses = []
        for _ in range(3):  # 多轮一致性调用
            response = openai.ChatCompletion.create(
                model=self.config["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )
            responses.append(response.choices[0].message['content'].strip())
        
        # 选择最一致的响应（简化实现）
        return max(set(responses), key=responses.count)
    
    def set_parameters(self, **kwargs):
        """动态更新LLM参数"""
        self.config.update(kwargs)