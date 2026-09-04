# -*- coding: utf-8 -*-
"""
美股拆股、分红数据抓取模块
使用 yfinance 获取免费数据
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_upcoming_splits_and_dividends(days_ahead: int = 7) -> Dict:
    """
    获取未来一段时间的拆股和分红事件
    
    Args:
        days_ahead: 向前查看的天数
    
    Returns:
        包含splits和dividends的字典
    """
    result = {
        "splits": [],
        "dividends": []
    }
    
    # 使用主要指数成分股作为监控范围
    tickers = get_major_us_tickers()
    
    end_date = datetime.now() + timedelta(days=days_ahead)
    
    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 获取拆股信息
            if info.get('stockSplitHistory') or info.get('lastStockSplit'):
                # 获取历史拆股记录（最近几年的）
                pass
            
            # 从info中获取
            last_split = info.get('lastStockSplit', {})
            if last_split:
                split_date = last_split.get('date', '')
                if split_date:
                    split_date_dt = datetime.strptime(split_date, '%Y-%m-%d')
                    if split_date_dt <= end_date and split_date_dt >= datetime.now():
                        result["splits"].append({
                            'symbol': ticker_symbol,
                            'name': info.get('shortName', ticker_symbol),
                            'ratio': last_split.get('ratio', 'N/A'),
                            'date': split_date
                        })
            
            # 获取分红信息
            dividends = ticker.dividends
            if not dividends.empty:
                # 获取最近的分红
                recent_div = dividends.iloc[-1]
                div_date = recent_div.name
                if isinstance(div_date, datetime):
                    div_date_str = div_date.strftime('%Y-%m-%d')
                    if div_date <= end_date and div_date >= datetime.now():
                        result["dividends"].append({
                            'symbol': ticker_symbol,
                            'name': info.get('shortName', ticker_symbol),
                            'amount': float(recent_div),
                            'date': div_date_str,
                            'yield': info.get('dividendYield', 0)
                        })
                        
        except Exception as e:
            logger.debug(f"Error fetching {ticker_symbol}: {e}")
            continue
    
    return result


def get_major_us_tickers() -> List[str]:
    """
    获取主要美股 ticker 列表
    这里使用主要指数成分股
    """
    # 主要上市公司 - 可按需扩展
    major_tickers = [
        # 科技巨头
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
        'ORCL', 'CRM', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'TXN', 'AVGO', 'NOW', 'SNOW',
        
        # 金融
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP', 'V', 'MA', 'PYPL', 'SQ',
        
        # 消费
        'WMT', 'HD', 'COST', 'TGT', 'LOW', 'NKE', 'SBUX', 'MCD', 'DIS', 'CMCSA',
        
        # 医疗
        'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'AMGN', 'GILD',
        
        # 能源
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'VLO',
        
        # 工业
        'BA', 'CAT', 'GE', 'HON', 'UPS', 'FDX', 'LMT', 'RTX',
        
        # 通信
        'T', 'VZ', 'TMUS',
        
        # 房地产
        'AMT', 'PLD', 'CCI', 'EQIX',
        
        # 公用事业
        'NEE', 'DUK', 'SO', 'D',
        
        # 更多科技
        'UBER', 'LYFT', 'ABNB', 'RBLX', 'PLTR', 'COIN', 'MARA', 'RIOT',
    ]
    return major_tickers


def check_ticker_events(ticker_symbol: str, target_date: str = None) -> Dict:
    """
    检查特定股票是否有拆股或分红事件
    
    Args:
        ticker_symbol: 股票代码
        target_date: 目标日期 (YYYY-MM-DD), 默认为今天
    
    Returns:
        事件信息字典
    """
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    events = {
        'symbol': ticker_symbol,
        'split': None,
        'dividend': None
    }
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 检查拆股
        if info.get('lastStockSplit'):
            split = info['lastStockSplit']
            if split.get('date') == target_date:
                events['split'] = {
                    'ratio': split.get('ratio'),
                    'date': split.get('date')
                }
        
        # 检查分红
        dividends = ticker.dividends
        if not dividends.empty:
            for date, amount in dividends.items():
                if date.strftime('%Y-%m-%d') == target_date:
                    events['dividend'] = {
                        'amount': float(amount),
                        'date': date.strftime('%Y-%m-%d')
                    }
                    break
        
    except Exception as e:
        logger.error(f"Error checking {ticker_symbol}: {e}")
    
    return events


def format_events_message(events_data: Dict) -> str:
    """
    格式化事件为飞书消息
    """
    if not events_data:
        return "📭 暂无今日美股拆股/分红事件"
    
    messages = []
    messages.append("📈 **美股今日Corporate Events**\n")
    
    # 分红
    if events_data.get('dividends'):
        messages.append("💰 **分红 (Dividends)**")
        for div in events_data['dividends']:
            yield_pct = div.get('yield', 0) * 100 if div.get('yield') else 0
            msg = f"- **{div['symbol']}** {div['name']}\n"
            msg += f"  分红: ${div['amount']:.4f}/股 | 日期: {div['date']}"
            if yield_pct > 0:
                msg += f" | 股息率: {yield_pct:.2f}%"
            messages.append(msg)
        messages.append("")
    
    # 拆股
    if events_data.get('splits'):
        messages.append("✂️ **拆股/并股 (Splits)**")
        for split in events_data['splits']:
            msg = f"- **{split['symbol']}** {split['name']}\n"
            msg += f"  比例: {split['ratio']} | 日期: {split['date']}"
            messages.append(msg)
        messages.append("")
    
    if not events_data.get('dividends') and not events_data.get('splits'):
        return "📭 暂无今日美股拆股/分红事件"
    
    return "\n".join(messages)


if __name__ == "__main__":
    # 测试
    data = get_upcoming_splits_and_dividends(7)
    print(f"Splits: {len(data['splits'])}")
    print(f"Dividends: {len(data['dividends'])}")
    print(format_events_message(data))