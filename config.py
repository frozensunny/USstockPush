# -*- coding: utf-8 -*-
"""
飞书美股信息推送配置
"""

# 飞书Webhook地址 (在飞书群创建机器人后获取)
# 本地运行时直接填写，GitHub Actions 会从 secrets 读取
import os
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")

# 推送时间 (小时, 24小时制)
PUSH_HOUR = 9  # 每天早上9点推送

# 搜索最近多少天的数据
DAYS_LOOKBACK = 7

# 是否只推送今日事件
ONLY_TODAY = False