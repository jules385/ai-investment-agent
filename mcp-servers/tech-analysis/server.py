"""
Tech Analysis MCP Server — A股技术分析指标服务
基于 ta 库 + pandas，提供 MACD/RSI/布林/KDJ/K线形态等15+技术指标
数据源: AKShare (免费)
"""

from datetime import datetime

import akshare as ak
import numpy as np
import pandas as pd
import ta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "tech-analysis",
    instructions="A股技术分析MCP服务 — 提供MACD/RSI/布林带/KDJ/K线形态/支撑阻力等指标"
)

# ── Helper ──────────────────────────────────────────────

def _get_kline(symbol: str, period: str = "daily", days: int = 250) -> pd.DataFrame:
    """获取K线数据
    symbol format: "002414" or "000858" (自动添加 sz/sh 前缀)
    """
    # Determine exchange prefix
    if symbol.startswith(('sz', 'sh')):
        ak_symbol = symbol
    elif symbol.startswith(('0', '3', '2')):
        ak_symbol = f"sz{symbol}"
    elif symbol.startswith(('6', '9')):
        ak_symbol = f"sh{symbol}"
    else:
        ak_symbol = f"sz{symbol}"

    try:
        if period == "weekly":
            # 周线: 用日线数据聚合
            df = ak.stock_zh_a_daily(symbol=ak_symbol, adjust="qfq")
            if df.empty:
                return pd.DataFrame()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            # Resample to weekly
            df_w = pd.DataFrame()
            df_w['open'] = df['open'].resample('W').first()
            df_w['high'] = df['high'].resample('W').max()
            df_w['low'] = df['low'].resample('W').min()
            df_w['close'] = df['close'].resample('W').last()
            df_w['volume'] = df['volume'].resample('W').sum()
            df_w['amount'] = df['amount'].resample('W').sum()
            if 'turnover' in df.columns:
                df_w['turnover'] = df['turnover'].resample('W').mean()
            df_w.dropna(inplace=True)
            return df_w.tail(days)
        elif period == "monthly":
            df = ak.stock_zh_a_daily(symbol=ak_symbol, adjust="qfq")
            if df.empty:
                return pd.DataFrame()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            df_m = pd.DataFrame()
            df_m['open'] = df['open'].resample('ME').first()
            df_m['high'] = df['high'].resample('ME').max()
            df_m['low'] = df['low'].resample('ME').min()
            df_m['close'] = df['close'].resample('ME').last()
            df_m['volume'] = df['volume'].resample('ME').sum()
            df_m['amount'] = df['amount'].resample('ME').sum()
            if 'turnover' in df.columns:
                df_m['turnover'] = df['turnover'].resample('ME').mean()
            df_m.dropna(inplace=True)
            return df_m.tail(days)
        else:
            # daily
            df = ak.stock_zh_a_daily(symbol=ak_symbol, adjust="qfq")
            if df.empty:
                return pd.DataFrame()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            return df.tail(days)
    except Exception as e:
        return pd.DataFrame()


def _safe_val(v, default=None):
    """Handle NaN/NaT values"""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return round(float(v), 4)
    return v


def _df_summary(df: pd.DataFrame, tail: int = 5) -> dict:
    """Convert DataFrame tail to dict for output"""
    records = []
    for idx, row in df.tail(tail).iterrows():
        rec = {}
        for col in df.columns:
            rec[col] = _safe_val(row[col])
        if isinstance(idx, pd.Timestamp):
            rec['date'] = idx.strftime("%Y-%m-%d")
        records.append(rec)
    return {"recent_data": records, "total_rows": len(df)}


# ── 工具 1: MA 均线 ────────────────────────────────────

@mcp.tool()
def compute_ma(symbol: str, period: str = "daily", days: int = 250, ma_windows: str = "5,10,20,60,120,250") -> dict:
    """
    计算移动平均线 MA(5/10/20/60/120/250)

    Args:
        symbol: 股票代码，如 "002414"
        period: K线周期 daily/weekly/monthly
        days: 获取数据天数
        ma_windows: 均线窗口，逗号分隔，默认 "5,10,20,60,120,250"
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    windows = [int(w.strip()) for w in ma_windows.split(",")]
    result = {"symbol": symbol, "period": period}

    close = df['close']
    for w in windows:
        ma = close.rolling(window=w).mean()
        result[f"MA{w}"] = _safe_val(round(float(ma.iloc[-1]), 2))
        # 价格相对于均线的位置
        if pd.notna(ma.iloc[-1]):
            pct = round((float(close.iloc[-1]) - float(ma.iloc[-1])) / float(ma.iloc[-1]) * 100, 2)
            result[f"MA{w}_偏离%"] = pct

    result["最新收盘价"] = _safe_val(round(float(close.iloc[-1]), 2))

    # 多头/空头排列判断
    ma_vals = [(w, float(close.rolling(window=w).mean().iloc[-1])) for w in windows if pd.notna(close.rolling(window=w).mean().iloc[-1])]
    ma_vals_sorted = sorted(ma_vals, key=lambda x: x[1], reverse=True)
    short_term = min(ma_vals, key=lambda x: x[0])
    long_term = max(ma_vals, key=lambda x: x[0])
    if short_term[1] > long_term[1]:
        result["均线形态"] = "多头排列 📈"
    else:
        result["均线形态"] = "空头排列 📉"

    return result


# ── 工具 2: MACD ────────────────────────────────────────

@mcp.tool()
def compute_macd(symbol: str, period: str = "daily", days: int = 250, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    计算 MACD 指标

    Args:
        symbol: 股票代码
        period: K线周期
        days: 数据天数
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    macd_indicator = ta.trend.MACD(
        close=df['close'],
        window_slow=slow,
        window_fast=fast,
        window_sign=signal
    )
    macd_line = macd_indicator.macd()
    signal_line = macd_indicator.macd_signal()
    histogram = macd_indicator.macd_diff()

    result = {
        "symbol": symbol,
        "period": period,
        "MACD_DIF": _safe_val(round(float(macd_line.iloc[-1]), 4)),
        "MACD_DEA": _safe_val(round(float(signal_line.iloc[-1]), 4)),
        "MACD_HIST": _safe_val(round(float(histogram.iloc[-1]), 4)),
        "最新收盘价": _safe_val(round(float(df['close'].iloc[-1]), 2)),
    }

    # 金叉/死叉判断
    if pd.notna(macd_line.iloc[-1]) and pd.notna(macd_line.iloc[-2]):
        prev_diff = float(macd_line.iloc[-2]) - float(signal_line.iloc[-2])
        curr_diff = float(macd_line.iloc[-1]) - float(signal_line.iloc[-1])
        if prev_diff < 0 and curr_diff > 0:
            result["信号"] = "金叉 ✨ (买入信号)"
        elif prev_diff > 0 and curr_diff < 0:
            result["信号"] = "死叉 ⚠️ (卖出信号)"
        elif curr_diff > 0:
            result["信号"] = "多头运行中"
        else:
            result["信号"] = "空头运行中"

    # 背离检测 (简化: 价格新高 MACD未新高)
    recent_close = df['close'].tail(20)
    recent_macd = macd_line.tail(20)
    price_high_idx = recent_close.idxmax()
    macd_high_idx = recent_macd.idxmax()
    if price_high_idx != macd_high_idx:
        result["背离警告"] = "⚠️ 价格与MACD走势不同步，可能存在背离"

    return result


# ── 工具 3: RSI ─────────────────────────────────────────

@mcp.tool()
def compute_rsi(symbol: str, period: str = "daily", days: int = 250, rsi_period: int = 14) -> dict:
    """
    计算 RSI 相对强弱指标

    Args:
        symbol: 股票代码
        period: K线周期
        days: 数据天数
        rsi_period: RSI周期，默认14
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    rsi = ta.momentum.RSIIndicator(close=df['close'], window=rsi_period)
    rsi_val = float(rsi.rsi().iloc[-1])

    result = {
        "symbol": symbol,
        "period": period,
        "RSI": round(rsi_val, 2),
        "最新收盘价": _safe_val(round(float(df['close'].iloc[-1]), 2)),
    }

    if rsi_val >= 80:
        result["区域"] = "严重超买 🔴"
        result["建议"] = "高位风险，关注减仓信号"
    elif rsi_val >= 70:
        result["区域"] = "超买区 🟠"
        result["建议"] = "短期可能回调"
    elif rsi_val >= 50:
        result["区域"] = "偏强区 🟡"
        result["建议"] = "趋势偏多"
    elif rsi_val >= 30:
        result["区域"] = "偏弱区 🟢"
        result["建议"] = "趋势偏空，等待企稳"
    elif rsi_val >= 20:
        result["区域"] = "超卖区 🔵"
        result["建议"] = "左侧分批布局机会"
    else:
        result["区域"] = "严重超卖 🔷"
        result["建议"] = "极度恐慌，关注反弹机会"

    # RSI 趋势
    rsi_5d = rsi.rsi().tail(5)
    if len(rsi_5d) >= 3:
        if all(rsi_5d.iloc[i] < rsi_5d.iloc[i+1] for i in range(len(rsi_5d)-1)):
            result["RSI趋势"] = "上升趋势 ↗️"
        elif all(rsi_5d.iloc[i] > rsi_5d.iloc[i+1] for i in range(len(rsi_5d)-1)):
            result["RSI趋势"] = "下降趋势 ↘️"
        else:
            result["RSI趋势"] = "震荡 ↔️"

    return result


# ── 工具 4: 布林带 ──────────────────────────────────────

@mcp.tool()
def compute_bollinger(symbol: str, period: str = "daily", days: int = 250, window: int = 20, n_std: float = 2.0) -> dict:
    """
    计算布林带 (Bollinger Bands)

    Args:
        symbol: 股票代码
        period: K线周期
        days: 数据天数
        window: 布林带窗口
        n_std: 标准差倍数
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    bb = ta.volatility.BollingerBands(close=df['close'], window=window, window_dev=n_std)
    upper = float(bb.bollinger_hband().iloc[-1])
    middle = float(bb.bollinger_mavg().iloc[-1])
    lower = float(bb.bollinger_lband().iloc[-1])
    close = float(df['close'].iloc[-1])

    bandwidth = (upper - lower) / middle * 100  # 带宽百分比
    position = (close - lower) / (upper - lower) * 100  # 价格在带内的位置%

    result = {
        "symbol": symbol,
        "period": period,
        "布林上轨": round(upper, 2),
        "布林中轨": round(middle, 2),
        "布林下轨": round(lower, 2),
        "最新收盘价": round(close, 2),
        "带宽%": round(bandwidth, 2),
        "价格位置%": round(position, 2),
    }

    if position >= 90:
        result["信号"] = "触及上轨 📌 — 短线超买，可能回调"
    elif position <= 10:
        result["信号"] = "触及下轨 📌 — 短线超卖，可能反弹"
    elif position >= 70:
        result["信号"] = "偏强区域 — 价格靠近上轨运行"
    elif position <= 30:
        result["信号"] = "偏弱区域 — 价格靠近下轨运行"
    else:
        result["信号"] = "中性区域 — 价格在布林带中轨附近"

    # 布林带收窄/扩张
    bb_5d_ago = ta.volatility.BollingerBands(close=df['close'].iloc[:-5], window=window, window_dev=n_std)
    bw_5d_ago = (float(bb_5d_ago.bollinger_hband().iloc[-1]) - float(bb_5d_ago.bollinger_lband().iloc[-1])) / float(bb_5d_ago.bollinger_mavg().iloc[-1]) * 100
    if bandwidth < bw_5d_ago * 0.9:
        result["布林形态"] = "收窄 ⏳ — 可能即将变盘"
    elif bandwidth > bw_5d_ago * 1.1:
        result["布林形态"] = "扩张 📊 — 波动加大"
    else:
        result["布林形态"] = "平稳"

    return result


# ── 工具 5: KDJ ─────────────────────────────────────────

@mcp.tool()
def compute_kdj(symbol: str, period: str = "daily", days: int = 250, k_period: int = 9) -> dict:
    """
    计算 KDJ 随机指标

    Args:
        symbol: 股票代码
        period: K线周期
        days: 数据天数
        k_period: KDJ周期，默认9
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    stoch = ta.momentum.StochasticOscillator(
        high=df['high'], low=df['low'], close=df['close'],
        window=k_period, smooth_window=3
    )
    k_val = float(stoch.stoch().iloc[-1])
    d_val = float(stoch.stoch_signal().iloc[-1])
    j_val = 3 * k_val - 2 * d_val

    result = {
        "symbol": symbol,
        "period": period,
        "K值": round(k_val, 2),
        "D值": round(d_val, 2),
        "J值": round(j_val, 2),
    }

    if k_val > 80 and d_val > 80:
        result["区域"] = "超买区 🔴"
    elif k_val < 20 and d_val < 20:
        result["区域"] = "超卖区 🔵"
    elif k_val > d_val:
        result["区域"] = "偏多"
    else:
        result["区域"] = "偏空"

    # 金叉/死叉
    if len(df) >= 2:
        k_prev = float(stoch.stoch().iloc[-2])
        d_prev = float(stoch.stoch_signal().iloc[-2])
        if k_prev <= d_prev and k_val > d_val:
            result["信号"] = "KDJ金叉 ✨"
        elif k_prev >= d_prev and k_val < d_val:
            result["信号"] = "KDJ死叉 ⚠️"
        else:
            result["信号"] = "KDJ维持当前方向"

    return result


# ── 工具 6: ATR 真实波幅 ────────────────────────────────

@mcp.tool()
def compute_atr(symbol: str, period: str = "daily", days: int = 120, atr_window: int = 14) -> dict:
    """
    计算 ATR 平均真实波幅 (波动率指标)

    Args:
        symbol: 股票代码
        period: K线周期
        days: 数据天数
        atr_window: ATR窗口
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    atr = ta.volatility.AverageTrueRange(
        high=df['high'], low=df['low'], close=df['close'],
        window=atr_window
    )
    atr_val = float(atr.average_true_range().iloc[-1])
    close = float(df['close'].iloc[-1])
    atr_pct = atr_val / close * 100

    result = {
        "symbol": symbol,
        "period": period,
        "ATR": round(atr_val, 2),
        "ATR占价格%": round(atr_pct, 2),
        "最新收盘价": round(close, 2),
    }

    if atr_pct > 5:
        result["波动水平"] = "高波动 🔴 — 适合短线交易"
    elif atr_pct > 2:
        result["波动水平"] = "中等波动 🟡"
    else:
        result["波动水平"] = "低波动 🟢 — 趋势可能启动中"

    # 止损建议 (2倍ATR)
    result["ATR止损上轨(2x)"] = round(close + 2 * atr_val, 2)
    result["ATR止损下轨(2x)"] = round(close - 2 * atr_val, 2)

    return result


# ── 工具 7: 成交量分析 ──────────────────────────────────

@mcp.tool()
def compute_volume(symbol: str, period: str = "daily", days: int = 120) -> dict:
    """
    成交量分析：量比、放量/缩量判断、换手率

    Args:
        symbol: 股票代码
        days: 数据天数
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    vol = df['volume']
    close = df['close']

    # 量比 (近5日均量 vs 近20日均量)
    vol_5ma = vol.tail(5).mean()
    vol_20ma = vol.tail(20).mean()
    vol_ratio = float(vol_5ma / vol_20ma) if vol_20ma > 0 else 1.0

    # 当日量 vs 5日均量
    if len(vol) >= 5:
        vol_today = float(vol.iloc[-1])
        vol_5avg = float(vol.tail(5).iloc[:-1].mean()) if len(vol) >= 6 else float(vol.tail(5).mean())
        day_ratio = vol_today / vol_5avg if vol_5avg > 0 else 1.0
    else:
        day_ratio = 1.0

    # 换手率
    turnover = float(df['turnover'].iloc[-1]) if 'turnover' in df.columns else None

    # 量价配合
    vol_trend = "放量" if vol_ratio > 1.2 else ("缩量" if vol_ratio < 0.8 else "正常")
    price_change = float(close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) >= 6 else 0

    result = {
        "symbol": symbol,
        "量比(5/20)": round(vol_ratio, 2),
        "当日量比(日/5均)": round(day_ratio, 2),
        "成交量趋势": vol_trend,
        "近5日价格变动%": round(price_change, 2),
    }

    if turnover is not None:
        result["换手率%"] = round(turnover, 2)

    # 量价关系研判
    if vol_trend == "放量" and price_change > 0:
        result["量价关系"] = "放量上涨 ✅ — 上涨动力充足"
    elif vol_trend == "放量" and price_change < 0:
        result["量价关系"] = "放量下跌 ⚠️ — 抛压较重"
    elif vol_trend == "缩量" and price_change > 0:
        result["量价关系"] = "缩量上涨 — 上涨乏力"
    elif vol_trend == "缩量" and price_change < 0:
        result["量价关系"] = "缩量下跌 — 抛压减轻"
    else:
        result["量价关系"] = "量价正常"

    return result


# ── 工具 8: 综合技术评分 ────────────────────────────────

@mcp.tool()
def technical_score(symbol: str, period: str = "daily", days: int = 250) -> dict:
    """
    综合技术面评分 (0-100分)
    整合MACD/RSI/布林/KDJ/均线/量价关系
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    close = df['close']
    score = 50  # 基准分
    signals = []

    # 1. MACD (20分)
    macd_ind = ta.trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    macd_l = macd_ind.macd()
    macd_s = macd_ind.macd_signal()
    macd_h = macd_ind.macd_diff()

    if float(macd_l.iloc[-1]) > float(macd_s.iloc[-1]):
        score += 10; signals.append("MACD多头 ✓ (+10)")
    else:
        score -= 10; signals.append("MACD空头 ✗ (-10)")

    if pd.notna(macd_h.iloc[-1]) and pd.notna(macd_h.iloc[-2]):
        if float(macd_h.iloc[-1]) > float(macd_h.iloc[-2]):
            score += 5; signals.append("MACD柱增长 ✓ (+5)")

    if float(macd_l.iloc[-1]) > 0:
        score += 5; signals.append("MACD零轴上方 ✓ (+5)")

    # 2. RSI (15分)
    rsi = ta.momentum.RSIIndicator(close=close, window=14)
    rsi_val = float(rsi.rsi().iloc[-1])
    if 40 <= rsi_val <= 60:
        score += 15; signals.append("RSI中性健康 ✓ (+15)")
    elif 30 <= rsi_val < 40:
        score += 8; signals.append("RSI偏低但可接受 ✓ (+8)")
    elif 60 < rsi_val <= 70:
        score += 5; signals.append("RSI偏高 ✗ (+5)")
    elif rsi_val < 30:
        score -= 5; signals.append("RSI超卖 ✗ (-5)")
    else:
        score -= 10; signals.append("RSI超买 ✗ (-10)")

    # 3. 均线 (20分)
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    if float(close.iloc[-1]) > float(ma20.iloc[-1]) > float(ma60.iloc[-1]):
        score += 20; signals.append("均线多头排列 ✓ (+20)")
    elif float(close.iloc[-1]) > float(ma20.iloc[-1]):
        score += 10; signals.append("站上MA20 ✓ (+10)")
    elif float(close.iloc[-1]) < float(ma60.iloc[-1]):
        score -= 15; signals.append("跌破MA60 ✗ (-15)")
    else:
        score += 0; signals.append("均线交织 → (0)")

    # 4. 布林带 (15分)
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    bb_upper = float(bb.bollinger_hband().iloc[-1])
    bb_lower = float(bb.bollinger_lband().iloc[-1])
    bb_pos = (float(close.iloc[-1]) - bb_lower) / (bb_upper - bb_lower) * 100
    if 30 <= bb_pos <= 70:
        score += 15; signals.append("布林带中性 ✓ (+15)")
    elif 10 <= bb_pos < 30:
        score += 8; signals.append("布林带偏低 ✓ (+8)")
    else:
        score += 0; signals.append("布林带极端 → (0)")

    # 5. 成交量 (10分)
    vol = df['volume']
    vol_ratio = float(vol.tail(5).mean() / vol.tail(20).mean())
    if 0.8 <= vol_ratio <= 1.5:
        score += 10; signals.append("成交量正常 ✓ (+10)")
    elif vol_ratio > 2:
        score += 3; signals.append("异常放量 ✗ (+3)")
    else:
        score += 5; signals.append("成交量可接受 ✓ (+5)")

    # 6. KDJ (10分)
    stoch = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=close, window=9, smooth_window=3)
    k_val = float(stoch.stoch().iloc[-1])
    d_val = float(stoch.stoch_signal().iloc[-1])
    if k_val > d_val and 20 < k_val < 80:
        score += 10; signals.append("KDJ金叉健康 ✓ (+10)")
    elif k_val < d_val and k_val > 80:
        score -= 5; signals.append("KDJ高位死叉 ✗ (-5)")
    else:
        score += 5; signals.append("KDJ中性 ✓ (+5)")

    # 7. 价格动量 (10分)
    ret_5d = float(close.iloc[-1] / close.iloc[-6] - 1) * 100
    ret_20d = float(close.iloc[-1] / close.iloc[-21] - 1) * 100
    if ret_5d > 0 and ret_20d > 0:
        score += 10; signals.append("短中期上涨趋势 ✓ (+10)")
    elif ret_5d > 0:
        score += 5; signals.append("短期反弹中 ✓ (+5)")
    elif ret_20d < -10:
        score -= 5; signals.append("中期跌幅较大 ✗ (-5)")

    # 限制分数范围
    score = max(0, min(100, score))

    # 评级
    if score >= 80:
        grade = "强烈看多 🟢"
    elif score >= 65:
        grade = "偏多 🟡"
    elif score >= 45:
        grade = "中性 ⚪"
    elif score >= 30:
        grade = "偏空 🟠"
    else:
        grade = "强烈看空 🔴"

    return {
        "symbol": symbol,
        "period": period,
        "综合评分": f"{score}/100",
        "评级": grade,
        "近期涨跌_5日%": round(ret_5d, 2),
        "近期涨跌_20日%": round(ret_20d, 2),
        "RSI(14)": round(rsi_val, 2),
        "MACD_DIF": _safe_val(round(float(macd_l.iloc[-1]), 4)),
        "MACD_HIST": _safe_val(round(float(macd_h.iloc[-1]), 4)),
        "信号明细": signals,
    }


# ── 工具 9: K线形态识别 ─────────────────────────────────

@mcp.tool()
def detect_patterns(symbol: str, period: str = "daily", days: int = 250) -> dict:
    """
    检测K线形态：锤子线、吞没、启明星、黄昏星、三只乌鸦等

    Args:
        symbol: 股票代码
        period: K线周期
        days: 数据天数
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    patterns = []
    recent = df.tail(10)

    # 最近3根K线
    for i in range(len(recent) - 2, len(recent)):
        idx = recent.index[i]
        o = float(recent['open'].iloc[i])
        c = float(recent['close'].iloc[i])
        h = float(recent['high'].iloc[i])
        l = float(recent['low'].iloc[i])
        body = abs(c - o)
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        total_range = h - l

        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)

        # 十字星
        if total_range > 0 and body / total_range < 0.1:
            patterns.append({"日期": date_str, "形态": "十字星 ⊕", "含义": "变盘信号"})
        # 锤子线
        elif total_range > 0 and lower_shadow > body * 2 and upper_shadow < body * 0.3 and c > o:
            patterns.append({"日期": date_str, "形态": "锤子线 🔨", "含义": "底部反转看涨"})
        # 吊颈线
        elif total_range > 0 and lower_shadow > body * 2 and upper_shadow < body * 0.3 and c < o:
            patterns.append({"日期": date_str, "形态": "吊颈线 ⚰️", "含义": "顶部反转看跌"})
        # 倒锤子
        elif total_range > 0 and upper_shadow > body * 2 and lower_shadow < body * 0.3 and c > o:
            patterns.append({"日期": date_str, "形态": "倒锤子 🔄", "含义": "底部反转看涨"})
        # 射击之星
        elif total_range > 0 and upper_shadow > body * 2 and lower_shadow < body * 0.3 and c < o:
            patterns.append({"日期": date_str, "形态": "射击之星 ☄️", "含义": "顶部反转看跌"})
        # 大阳线
        elif body / total_range > 0.7 and c > o and body > df['close'].iloc[-10:].std():
            patterns.append({"日期": date_str, "形态": "大阳线 ☀️", "含义": "强势上涨"})
        # 大阴线
        elif body / total_range > 0.7 and c < o and body > df['close'].iloc[-10:].std():
            patterns.append({"日期": date_str, "形态": "大阴线 🌧️", "含义": "强势下跌"})

    # 吞没形态 (近2根)
    if len(recent) >= 2:
        o1, c1 = float(recent['open'].iloc[-2]), float(recent['close'].iloc[-2])
        o2, c2 = float(recent['open'].iloc[-1]), float(recent['close'].iloc[-1])
        if c1 < o1 and c2 > o2 and abs(c2-o2) > abs(c1-o1):
            patterns.insert(0, {"日期": recent.index[-1].strftime("%Y-%m-%d"), "形态": "看涨吞没 🔥", "含义": "强烈反转看涨信号"})
        elif c1 > o1 and c2 < o2 and abs(c2-o2) > abs(c1-o1):
            patterns.insert(0, {"日期": recent.index[-1].strftime("%Y-%m-%d"), "形态": "看跌吞没 💥", "含义": "强烈反转看跌信号"})

    return {
        "symbol": symbol,
        "检测到的形态": patterns if patterns else [{"形态": "无显著形态", "含义": "近3日无明显K线形态信号"}],
        "形态数量": len(patterns),
    }


# ── 工具 10: 支撑/阻力位 ─────────────────────────────────

@mcp.tool()
def support_resistance(symbol: str, period: str = "daily", days: int = 250) -> dict:
    """
    基于历史高低点、均线、布林带计算支撑位和阻力位

    Args:
        symbol: 股票代码
    """
    df = _get_kline(symbol, period, days)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的K线数据"}

    close = float(df['close'].iloc[-1])

    # 历史高低点
    high_20d = float(df['high'].tail(20).max())
    low_20d = float(df['low'].tail(20).min())
    high_60d = float(df['high'].tail(60).max())
    low_60d = float(df['low'].tail(60).min())

    # 均线支撑
    ma20 = float(close.rolling(20).mean().iloc[-1]) if hasattr(close, 'rolling') else close
    ma60 = float(close.rolling(60).mean().iloc[-1]) if len(df) >= 60 and hasattr(close, 'rolling') else close
    ma120 = float(close.rolling(120).mean().iloc[-1]) if len(df) >= 120 and hasattr(close, 'rolling') else close

    # 布林带
    bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    bb_upper = float(bb.bollinger_hband().iloc[-1])
    bb_lower = float(bb.bollinger_lband().iloc[-1])

    resistances = []
    supports = []

    for name, val in [("前20日高", high_20d), ("布林上轨", bb_upper),
                       ("前60日高", high_60d)]:
        if val > close:
            resistances.append({"位": name, "价格": round(val, 2), "距离%": round((val/close-1)*100, 2)})

    for name, val in [("布林下轨", bb_lower), ("前20日低", low_20d),
                       ("MA60均线", ma60), ("MA120均线", ma120),
                       ("前60日低", low_60d)]:
        if val < close:
            supports.append({"位": name, "价格": round(val, 2), "距离%": round((close/val-1)*100, 2)})

    resistances.sort(key=lambda x: x["价格"])
    supports.sort(key=lambda x: x["价格"], reverse=True)

    return {
        "symbol": symbol,
        "当前价格": round(close, 2),
        "阻力位": resistances[:3],
        "支撑位": supports[:3],
    }


# ── Main ─────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
