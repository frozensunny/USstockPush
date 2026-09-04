# -*- coding: utf-8 -*-
"""
飞书机器人消息发送模块
"""

import requests
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FeishuBot:
    """飞书机器人"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
    
    def send_text(self, text: str) -> bool:
        """
        发送文本消息
        
        Args:
            text: 消息内容
        
        Returns:
            是否发送成功
        """
        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        return self._send(payload)
    
    def send_rich_text(self, title: str, content: list) -> bool:
        """
        发送富文本消息
        
        Args:
            title: 标题
            content: 内容列表, 每项为 [类型, 内容]
                    类型: "at", "text", "a"
        
        Returns:
            是否发送成功
        """
        # 富文本消息结构
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content
                    }
                }
            }
        }
        return self._send(payload)
    
    def send_card(self, title: str, elements: list) -> bool:
        """
        发送卡片消息
        
        Args:
            title: 卡片标题
            elements: 卡片元素列表
        
        Returns:
            是否发送成功
        """
        card = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title,
                    "template": "blue"
                }
            },
            "elements": elements
        }
        
        payload = {
            "msg_type": "interactive",
            "card": card
        }
        return self._send(payload)
    
    def send_corporate_events_card(self, splits: list, dividends: list) -> bool:
        """
        发送美股事件卡片消息
        
        Args:
            splits: 拆股列表
            dividends: 分红列表
        
        Returns:
            是否发送成功
        """
        elements = []
        
        # 添加时间戳
        from datetime import datetime
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        })
        elements.append({"tag": "hr"})
        
        # 分红部分
        if dividends:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "💰 **分红 Dividends**"
                }
            })
            for div in dividends:
                yield_pct = div.get('yield', 0) * 100 if div.get('yield') else 0
                content = f"🔹 **{div['symbol']}** {div['name']}\n"
                content += f"   分红: **${div['amount']:.4f}**/股 | 日期: {div['date']}"
                if yield_pct > 0:
                    content += f" | 股息率: {yield_pct:.2f}%"
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                })
        else:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "💰 分红: 暂无"
                }
            })
        
        elements.append({"tag": "hr"})
        
        # 拆股部分
        if splits:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "✂️ **拆股/并股 Splits**"
                }
            })
            for split in splits:
                content = f"🔹 **{split['symbol']}** {split['name']}\n"
                content += f"   比例: **{split['ratio']}** | 日期: {split['date']}"
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                })
        else:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "✂️ 拆股/并股: 暂无"
                }
            })
        
        # 添加底部提示
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "📌 数据来源: Yahoo Finance | 监控范围: 主要美股上市公司"
            }
        })
        
        return self.send_card("📈 美股今日Corporate Events", elements)
    
    def _send(self, payload: dict) -> bool:
        """发送请求"""
        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload).encode('utf-8'),
                headers=self.headers,
                timeout=10
            )
            result = response.json()
            
            if result.get('code') == 0:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送异常: {e}")
            return False


def test_webhook(webhook_url: str) -> bool:
    """测试Webhook是否可用"""
    bot = FeishuBot(webhook_url)
    return bot.send_text("✅ 飞书机器人配置成功！")


if __name__ == "__main__":
    # 测试
    import config
    test_webhook(config.FEISHU_WEBHOOK_URL)