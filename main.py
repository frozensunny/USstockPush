# -*- coding: utf-8 -*-
"""
美股信息飞书推送 - 主程序
"""

import config
from stock_fetcher import quick_check, get_us_stock_list, format_events_message
from feishu_sender import FeishuBot, test_webhook

def main():
    """主函数"""
    print("=" * 50)
    print("美股Corporate Events 推送程序")
    print("=" * 50)

    # 初始化飞书机器人
    bot = FeishuBot(config.FEISHU_WEBHOOK_URL)

    # 获取数据 - 先检查全量列表
    print("获取 NASDAQ + NYSE 股票列表...")
    all_tickers = get_us_stock_list()
    print(f"共 {len(all_tickers)} 只股票")

    # 列出所有股票
    print("\n📋 股票列表:")
    print("-" * 40)
    for i, ticker in enumerate(all_tickers, 1):
        print(f"{i:4d}. {ticker}")
    print("-" * 40)
    print(f"总计: {len(all_tickers)} 只\n")

    print(f"正在查询最近 {config.DAYS_LOOKBACK} 天的事件...")
    events = quick_check(tickers=all_tickers, days=config.DAYS_LOOKBACK)

    splits_count = len(events.get('splits', []))
    dividends_count = len(events.get('dividends', []))

    print(f"📊 查询结果:")
    print(f"   拆股: {splits_count} 条")
    print(f"   分红: {dividends_count} 条")

    # 发送到飞书
    print("\n正在推送到飞书...")
    success = bot.send_corporate_events_card(
        splits=events.get('splits', []),
        dividends=events.get('dividends', [])
    )

    if success:
        print("✅ 推送成功!")
    else:
        print("❌ 推送失败, 请检查配置")

    return success

if __name__ == "__main__":
    # 测试运行
    main()
