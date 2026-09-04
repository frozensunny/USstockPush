# 美股信息飞书推送

每天自动推送美股拆股(Stock Split)、并股(Reverse Split)、分红(Dividend)等信息到飞书群。

## 功能

- 📈 监控主要美股上市公司的拆股事件
- 💰 监控分红发放信息
- 🤖 自动推送到飞书群

## 快速开始

### 1. 安装依赖

```bash
pip install yfinance requests schedule
```

### 2. 配置飞书机器人

1. 打开飞书 desktop
2. 进入群设置 → 群机器人 → 添加机器人 → 自定义机器人
3. 设置机器人名称（如"美股推送"）
4. 复制 Webhook 地址
5. 修改 `config.py` 中的 `FEISHU_WEBHOOK_URL`

### 3. 运行测试

```bash
python main.py
```

### 4. 设置定时任务

#### macOS/Linux (crontab)

```bash
crontab -e
# 添加以下行: 每天早上9点执行
0 9 * * * /usr/bin/python3 /Users/zard/Documents/us_stock_notifier/main.py >> /Users/zard/Documents/us_stock_notifier/app.log 2>&1
```

#### 使用 launchd (macOS)

创建 `~/Library/LaunchAgents/com.usstock.notifier.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.usstock.notifier</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/zard/Documents/us_stock_notifier/main.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

加载:
```bash
launchctl load ~/Library/LaunchAgents/com.usstock.notifier.plist
```

## 文件结构

```
us_stock_notifier/
├── config.py          # 配置文件
├── stock_fetcher.py   # 数据抓取
├── feishu_sender.py   # 飞书发送
├── main.py            # 主程序
└── README.md
```

## 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| FEISHU_WEBHOOK_URL | 飞书Webhook地址 | (必填) |
| PUSH_HOUR | 推送时间(小时) | 9 |
| DAYS_LOOKBACK | 查询天数 | 7 |

## 监控股票范围

目前监控约70只主要美股:
- 科技: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA 等
- 金融: JPM, BAC, WFC, V, MA 等
- 消费: WMT, HD, COST, NKE 等
- 医疗: UNH, JNJ, PFE, ABBV 等
- 能源: XOM, CVX, COP 等

如需扩展，修改 `stock_fetcher.py` 中的 `get_major_us_tickers()` 函数。