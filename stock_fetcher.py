# -*- coding: utf-8 -*-
"""
美股拆股、分红数据抓取模块
支持全量 NASDAQ + NYSE 股票监控
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 股票列表缓存
_stock_list_cache = None


# 备用股票列表 (当无法从网络获取时使用)
FALLBACK_TICKERS = [
    # NASDAQ 主要股票
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD',
    'INTC', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'TXN', 'AVGO', 'NOW',
    'SNOW', 'UBER', 'LYFT', 'ABNB', 'RBLX', 'PLTR', 'COIN', 'MARA', 'RIOT', 'SQ',
    'PYPL', 'ZM', 'DOCU', 'TWLO', 'SHOP', 'WDAY', 'OKTA', 'DDOG', 'CRWD', 'NET',
    'TEAM', 'ATVI', 'BKNG', 'ISRG', 'REGN', 'VRTX', 'ALGN', 'ILMN', 'MRNA', 'LCID',
    'PENN', 'MGM', 'WYNN', 'LVS', 'MAR', 'HLT', 'EXPE', 'TRIP', 'ABNB', 'DASH',
    # NYSE 主要股票
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP', 'V', 'MA', 'BRK.B', 'BRK.A',
    'WMT', 'HD', 'COST', 'TGT', 'LOW', 'NKE', 'SBUX', 'MCD', 'DIS', 'CMCSA',
    'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'AMGN', 'GILD', 'BMY',
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'VLO', 'PSX', 'OXY',
    'BA', 'CAT', 'GE', 'HON', 'UPS', 'FDX', 'LMT', 'RTX', 'NOC', 'GD',
    'T', 'VZ', 'TMUS',
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL',
    'NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'EXC', 'XEL',
    'KO', 'PEP', 'MCO', 'SPGI', 'MMC', 'SCHW', 'AXP', 'USB', 'TFC', 'COF',
    'DE', 'EMR', 'ITW', 'ETN', 'PH', 'ROK', 'CMI', 'AME', 'FTV',
    'AIG', 'MET', 'PRU', 'AFL', 'TRV', 'CIG', 'LNC', 'MET', 'GL',
    'MMM', 'GE', 'CAT', 'BA', 'HON', 'UPS', 'UNP',
    'F', 'GM', 'TM', 'HMC', 'RACE', 'FCAU',
]

def get_us_stock_list() -> List[str]:
    """
    获取所有 NASDAQ + NYSE 股票代码列表
    数据来源: rreichel3/US-Stock-Symbols (GitHub)
    """
    global _stock_list_cache
    
    if _stock_list_cache is not None:
        return _stock_list_cache
    
    tickers = set()
    
    # 从 GitHub 获取 NASDAQ 股票列表
    try:
        nasdaq_url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq_full_ticker.json"
        resp = requests.get(nasdaq_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                if item.get('symbol'):
                    tickers.add(item['symbol'].strip().upper())
            logger.info(f"获取到 {len(data)} 只 NASDAQ 股票")
    except Exception as e:
        logger.warning(f"获取 NASDAQ 列表失败: {e}")
    
    # 从 GitHub 获取 NYSE 股票列表
    try:
        nyse_url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse_full_ticker.json"
        resp = requests.get(nyse_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                if item.get('symbol'):
                    tickers.add(item['symbol'].strip().upper())
            logger.info(f"获取到 {len(data)} 只 NYSE 股票")
    except Exception as e:
        logger.warning(f"获取 NYSE 列表失败: {e}")
    
    # 如果获取失败，使用备用列表
    if len(tickers) < 100:
        logger.warning("使用备用股票列表")
        tickers = set(FALLBACK_TICKERS)
    
    # 过滤掉非法字符
    valid_tickers = []
    for t in tickers:
        if t and (t.isalpha() or t.isalnum()) and not t.endswith('-'):
            valid_tickers.append(t)
    
    _stock_list_cache = sorted(valid_tickers)
    logger.info(f"共获取 {len(_stock_list_cache)} 只美股")
    return _stock_list_cache


def check_ticker_events(ticker_symbol: str, start_date: datetime, end_date: datetime) -> Dict:
    """
    检查单只股票是否有拆股或分红事件
    """
    result = {
        'symbol': ticker_symbol,
        'split': None,
        'dividend': None,
        'error': None
    }
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # 获取股票名称
        try:
            info = ticker.info
            result['name'] = info.get('shortName', info.get('longName', ticker_symbol))
        except:
            result['name'] = ticker_symbol
        
        # 获取分红
        dividends = ticker.dividends
        if not dividends.empty:
            # 筛选日期范围内的分红
            mask = (dividends.index >= start_date) & (dividends.index <= end_date)
            recent = dividends[mask]
            if not recent.empty:
                latest = recent.iloc[-1]
                result['dividend'] = {
                    'amount': float(latest),
                    'date': latest.name.strftime('%Y-%m-%d')
                }
        
        # 获取拆股 - 通过 info 获取最近的拆股
        # 注意: yfinance 不直接提供未来拆股预告，这里获取历史记录
        # 实际使用时需结合其他数据源获取预告
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_upcoming_events(days_ahead: int = 7, max_workers: int = 50) -> Dict:
    """
    获取未来一段时间的拆股和分红事件
    
    Args:
        days_ahead: 向前查看的天数
        max_workers: 并行线程数
    
    Returns:
        包含splits和dividends的字典
    """
    result = {
        "splits": [],
        "dividends": []
    }
    
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=days_ahead)
    
    # 获取股票列表
    tickers = get_us_stock_list()
    logger.info(f"开始检查 {len(tickers)} 只股票...")
    
    # 并行检查
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_ticker_events, t, start_date, end_date): t 
            for t in tickers
        }
        
        for future in as_completed(futures):
            completed += 1
            if completed % 500 == 0:
                logger.info(f"进度: {completed}/{len(tickers)}")
            
            try:
                events = future.result()
                
                # 处理分红
                if events.get('dividend'):
                    result["dividends"].append({
                        'symbol': events['symbol'],
                        'name': events.get('name', events['symbol']),
                        'amount': events['dividend']['amount'],
                        'date': events['dividend']['date'],
                        'yield': 0  # 简化处理
                    })
                
                # 处理拆股 (如果有)
                # 注意: yfinance 的 stockSplitHistory 需要特殊处理
                
            except Exception as e:
                continue
    
    logger.info(f"查询完成: 分红 {len(result['dividends'])} 条, 拆股 {len(result['splits'])} 条")
    return result


# 以下为精简版 - 只检查主要股票，适合快速测试
def get_major_us_tickers() -> List[str]:
    """主要美股 ticker 列表 (精简版)"""
    return [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD',
        'INTC', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'TXN', 'AVGO', 'NOW',
        'SNOW', 'UBER', 'LYFT', 'ABNB', 'RBLX', 'PLTR', 'COIN', 'MARA', 'RIOT', 'SQ',
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP', 'V', 'MA', 'PYPL',
        'WMT', 'HD', 'COST', 'TGT', 'LOW', 'NKE', 'SBUX', 'MCD', 'DIS', 'CMCSA',
        'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'AMGN', 'GILD',
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'VLO',
        'BA', 'CAT', 'GE', 'HON', 'UPS', 'FDX', 'LMT', 'RTX',
        'T', 'VZ', 'TMUS',
        'AMT', 'PLD', 'CCI', 'EQIX',
        'NEE', 'DUK', 'SO', 'D',
    ]


def quick_check(tickers: List[str] = None, days: int = 7, max_tickers: int = 200) -> Dict:
    """
    快速检查 - 使用精简列表，只检查最近有分红的股票
    """
    if tickers is None:
        tickers = get_major_us_tickers()
    
    # 限制股票数量，避免超时
    tickers = tickers[:max_tickers]
    
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=days)
    
    result = {"splits": [], "dividends": []}
    
    # 使用多线程加速
    def check_one(symbol):
        try:
            return check_ticker_events(symbol, start_date, end_date)
        except:
            return None
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_one, t): t for t in tickers}
        for i, future in enumerate(as_completed(futures)):
            try:
                events = future.result()
                if events and events.get('dividend'):
                    result["dividends"].append({
                        'symbol': events['symbol'],
                        'name': events.get('name', events['symbol']),
                        'amount': events['dividend']['amount'],
                        'date': events['dividend']['date'],
                        'yield': 0
                    })
            except:
                continue
            # 限制结果数量
            if len(result["dividends"]) >= 50:
                break
    
    return result


def format_events_message(events_data: Dict) -> str:
    """
    格式化事件为飞书消息
    """
    if not events_data:
        return "📭 暂无美股拆股/分红事件"
    
    messages = []
    messages.append("📈 **美股Corporate Events**\n")
    
    # 分红
    if events_data.get('dividends'):
        messages.append("💰 **分红 (Dividends)**")
        for div in events_data['dividends']:
            msg = f"- **{div['symbol']}** {div['name']}\n"
            msg += f"  分红: ${div['amount']:.4f}/股 | 日期: {div['date']}"
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
        return "📭 暂无美股拆股/分红事件"
    
    return "\n".join(messages)
