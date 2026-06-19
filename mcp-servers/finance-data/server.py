"""
Finance Data MCP Server — A股基本面数据服务
数据源优先级：East Money(主) → 同花顺 → 腾讯/搜狐(回退)
内置请求节流(2s间隔)和自动回退机制
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("finance-data",
    instructions="A股基本面数据 — East Money主源+自动回退。调用间隔已内置节流。")

_last_call = 0

def _throttle():
    """确保两次API调用间隔至少2秒，避免East Money限流"""
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < 2.0:
        time.sleep(2.0 - elapsed)
    _last_call = time.time()

def _safe(v, default=None):
    if v is None or (isinstance(v, float) and np.isnan(v)): return default
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return round(float(v), 4)
    return v

def _get_symbol(symbol: str) -> str:
    symbol = symbol.strip()
    if symbol.startswith(('sz', 'sh', 'bj')): return symbol
    if symbol.startswith(('0', '3', '2')): return f"sz{symbol}"
    if symbol.startswith(('6', '9')): return f"sh{symbol}"
    if symbol.startswith(('4', '8')): return f"bj{symbol}"  # 北交所
    return f"sz{symbol}"

# ── 工具 1: 历史行情（East Money主→腾讯回退）─────────

@mcp.tool()
def get_historical_data(symbol: str, days: int = 250) -> dict:
    """
    获取历史日K线（East Money主源，自动回退腾讯）

    Args:
        symbol: 股票代码，如 "002414"
        days: 获取天数
    """
    _throttle()
    try:
        # 主源：East Money
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=(datetime.now().replace(year=datetime.now().year-2)).strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"),
            adjust="qfq"
        )
        if df.empty: raise ValueError("Empty")
        source = "eastmoney"
    except:
        # 回退：腾讯
        try:
            ak_symbol = _get_symbol(symbol)
            df = ak.stock_zh_a_daily(symbol=ak_symbol, adjust="qfq")
            if df.empty: return {"error": f"No data for {symbol}"}
            source = "tencent/sohu"
        except:
            return {"error": f"All sources failed for {symbol}"}

    if 'date' not in df.columns:
        # East Money returns Chinese column names
        col_map = {'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high',
                   '最低': 'low', '成交量': 'volume', '成交额': 'amount', '换手率': 'turnover'}
        df.rename(columns={k:v for k,v in col_map.items() if k in df.columns}, inplace=True)

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    df = df.tail(days)

    latest = df.iloc[-1]
    return {
        "symbol": symbol, "source": source, "rows": len(df),
        "date_range": f"{str(df.index[0].date())} ~ {str(df.index[-1].date())}",
        "latest_price": _safe(round(float(latest['close']), 2)),
        "latest_volume": _safe(int(latest['volume'])) if 'volume' in df else None,
        "high_52w": _safe(round(float(df['high'].tail(250).max()), 2)),
        "low_52w": _safe(round(float(df['low'].tail(250).min()), 2)),
        "change_5d": _safe(round(float((latest['close']/df['close'].iloc[-6]-1)*100), 2)) if len(df)>=6 else None,
        "change_20d": _safe(round(float((latest['close']/df['close'].iloc[-21]-1)*100), 2)) if len(df)>=21 else None,
    }

# ── 工具 2: 财务指标（同花顺源）─────────────────────

@mcp.tool()
def get_financial_indicators(symbol: str) -> dict:
    """
    获取核心财务指标（同花顺数据源，稳定可靠）

    Args:
        symbol: 股票代码
    """
    _throttle()
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df.empty: return {"error": f"No financial data for {symbol}"}

        latest = df.iloc[-1]  # 最后一行是最新数据
        def _col(name_part):
            for c in df.columns:
                if name_part in c: return _safe(latest[c])
            return None

        return {
            "symbol": symbol, "source": "tonghuashun",
            "report_period": str(latest.iloc[0]) if len(latest) > 0 else "N/A",
            "revenue": _col('营业总收入'),
            "revenue_yoy": _col('同比增长'),
            "net_profit": _col('归母净利润'),
            "net_profit_yoy": _col('归母净利润同比增长'),
            "deducted_net_profit": _col('扣非净利润'),
            "gross_margin": _col('毛利率'),
            "net_margin": _col('净利率'),
            "roe": _col('ROE'),
            "eps": _col('每股收益'),
            "debt_ratio": _col('资产负债率'),
            "operating_cf_per_share": _col('每股经营性现金流'),
            "total_reports": len(df),
        }
    except Exception as e:
        return {"error": str(e)[:100]}

# ── 工具 2b: 财务指标历史序列（同花顺源，多期）─────

@mcp.tool()
def get_financial_history(symbol: str, periods: int = 8) -> dict:
    """
    获取最近N期财务指标时间序列（同花顺源），用于季度对比和趋势分析

    Args:
        symbol: 股票代码
        periods: 返回最近N期数据（默认8期=2年季度数据）
    """
    _throttle()
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df.empty: return {"error": f"No financial data for {symbol}"}

        recent = df.tail(min(periods, len(df)))

        def _col_data(col_name, row):
            for c in df.columns:
                if col_name in c: return _safe(row[c])
            return None

        quarters = []
        for _, row in recent.iterrows():
            q = {
                "period": str(row.iloc[0]) if len(row) > 0 else "N/A",
                "revenue": _col_data('营业总收入', row),
                "revenue_yoy": _col_data('同比增长', row),
                "net_profit": _col_data('归母净利润', row),
                "net_profit_yoy": _col_data('归母净利润同比增长', row),
                "deducted_net_profit": _col_data('扣非净利润', row),
                "gross_margin": _col_data('毛利率', row),
                "net_margin": _col_data('净利率', row),
                "roe": _col_data('ROE', row),
                "eps": _col_data('每股收益', row),
                "debt_ratio": _col_data('资产负债率', row),
                "operating_cf_per_share": _col_data('每股经营性现金流', row),
                "rd_expense_ratio": _col_data('研发费用', row),
            }
            # 尝试从扣非净利润列推断同比
            try:
                for c in df.columns:
                    if '扣非' in c and '同比' in c:
                        q["deducted_yoy"] = _safe(row[c])
                        break
            except: pass
            quarters.append(q)

        return {
            "symbol": symbol,
            "source": "tonghuashun",
            "periods_returned": len(quarters),
            "total_available": len(df),
            "date_range": f"{quarters[0]['period']} ~ {quarters[-1]['period']}" if quarters else "N/A",
            "quarters": quarters,
        }
    except Exception as e:
        return {"error": str(e)[:100]}

# ── 工具 3: 估值数据 ──────────────────────────────────

@mcp.tool()
def get_valuation(symbol: str) -> dict:
    """
    获取估值（PE/PB/市值），基于行情+财务数据计算

    Args:
        symbol: 股票代码
    """
    _throttle()
    try:
        ak_symbol = _get_symbol(symbol)
        df = ak.stock_zh_a_daily(symbol=ak_symbol, adjust="qfq")
        if df.empty: return {"error": f"No data for {symbol}"}

        latest = df.iloc[-1]
        price = float(latest['close'])
        shares = float(latest.get('outstanding_share', 0))
        mcap = round(price * shares / 1e8, 2) if shares > 0 else None

        # Try getting EPS from THS data
        eps = None
        try:
            fin = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
            if not fin.empty:
                for c in fin.columns:
                    if '每股收益' in c:
                        eps = float(fin.iloc[0][c])
                        break
        except: pass

        return {
            "symbol": symbol, "price": round(price, 2),
            "pe_ttm": round(price / eps, 2) if eps and eps > 0 else None,
            "eps_ttm": round(eps, 4) if eps else None,
            "market_cap_billion": mcap,
            "source": "tencent+ths",
        }
    except Exception as e:
        return {"error": str(e)[:100]}

# ── 工具 4: 股东数据（East Money，可能不稳定）─────────

@mcp.tool()
def get_shareholders(symbol: str) -> dict:
    """
    获取前十大股东及股东户数趋势（East Money源，自动重试3次）

    Args:
        symbol: 股票代码
    """
    holders_list = []
    for attempt in range(3):
        _throttle()
        try:
            df = ak.stock_main_stock_holder(stock=symbol)
            if not df.empty:
                for _, row in df.head(10).iterrows():
                    holders_list.append({
                        "name": str(row.get('股东名称', '')),
                        "shares": _safe(row.get('持股数', row.get('持股数量', 0))),
                        "ratio": _safe(row.get('持股比例', row.get('占总股本比例', 0))),
                    })
                break
        except Exception as e:
            if attempt == 2:
                holders_list = [{"error": f"Failed after 3 attempts: {str(e)[:80]}"}]
            time.sleep(3)

    # 股东户数趋势（腾讯/同花顺源）
    holder_trend = []
    try:
        trend = ak.stock_shareholder_change_ths(symbol=symbol)
        if not trend.empty:
            for _, row in trend.head(4).iterrows():
                holder_trend.append({
                    "period": str(row.get('报告期', row.iloc[0] if len(row)>0 else '')),
                    "count": _safe(int(row.get('股东户数', 0)) if '股东户数' in trend.columns else None),
                })
    except: pass

    return {
        "symbol": symbol,
        "top10_holders": holders_list,
        "shareholder_trend": holder_trend,
        "source": "eastmoney(holders)+ths(trend)",
    }

# ── 工具 5: 龙虎榜（East Money）──────────────────────

@mcp.tool()
def get_lhb_details(symbol: str, recent_days: int = 90) -> dict:
    """
    获取龙虎榜明细（East Money源，带重试）

    Args:
        symbol: 股票代码
        recent_days: 查询最近N天
    """
    for attempt in range(3):
        _throttle()
        try:
            df = ak.stock_lhb_stock_detail_em(symbol=symbol, recent_days=str(recent_days))
            if df.empty: return {"symbol": symbol, "lhb_entries": [], "note": "近期未上榜"}

            entries = []
            for _, row in df.head(10).iterrows():
                entries.append({
                    "date": str(row.get('上榜日期', '')),
                    "buy_amount": _safe(row.get('买入金额', 0)),
                    "sell_amount": _safe(row.get('卖出金额', 0)),
                    "net_amount": _safe(row.get('净买额', 0)),
                    "reason": str(row.get('上榜原因', '')),
                })
            return {"symbol": symbol, "lhb_entries": entries, "source": "eastmoney"}
        except Exception as e:
            if attempt == 2: return {"error": str(e)[:100]}
            time.sleep(3)

# ── 工具 6: 个股资金流向（East Money）─────────────────

@mcp.tool()
def get_fund_flow(symbol: str) -> dict:
    """
    获取个股资金流向：主力/超大单/大单/中单/小单（East Money源，带重试）

    Args:
        symbol: 股票代码
    """
    for attempt in range(3):
        _throttle()
        try:
            df = ak.stock_individual_fund_flow(symbol=symbol, market="sz" if symbol.startswith(('0','3','2')) else "sh")
            if df.empty: return {"error": "No fund flow data"}

            recent = df.tail(20)
            main_net = _safe(round(float(recent['主力净流入-净额'].sum()) / 1e8, 2)) if '主力净流入-净额' in recent.columns else None
            super_large_net = _safe(round(float(recent['超大单净流入-净额'].sum()) / 1e8, 2)) if '超大单净流入-净额' in recent.columns else None

            return {
                "symbol": symbol,
                "period": "近20日累计",
                "main_net_inflow_billion": main_net,
                "super_large_net_inflow_billion": super_large_net,
                "source": "eastmoney",
            }
        except Exception as e:
            if attempt == 2: return {"error": str(e)[:100]}
            time.sleep(3)

# ── 工具 7: 融资融券（East Money）─────────────────────

@mcp.tool()
def get_margin_data(symbol: str) -> dict:
    """
    获取融资融券余额（East Money源，带重试）

    Args:
        symbol: 股票代码
    """
    for attempt in range(3):
        _throttle()
        try:
            exchange = "sse" if symbol.startswith('6') else "szse"
            fn = ak.stock_margin_detail_sse if exchange == "sse" else ak.stock_margin_detail_szse
            df = fn(symbol=symbol)

            if df.empty: return {"error": "No margin data"}
            latest = df.iloc[-1]
            return {
                "symbol": symbol,
                "margin_balance": _safe(round(float(latest.get('融资余额', 0)) / 1e8, 2)),
                "short_balance": _safe(round(float(latest.get('融券余量', 0)), 2)),
                "source": "eastmoney",
            }
        except Exception as e:
            if attempt == 2: return {"error": str(e)[:100]}
            time.sleep(3)

# ── 工具 8: 北向资金持仓（East Money）─────────────────

@mcp.tool()
def get_hsgt_holdings(symbol: str) -> dict:
    """
    获取北向资金（沪深港通）个股持仓及变化（East Money源，带重试）

    Args:
        symbol: 股票代码
    """
    for attempt in range(3):
        _throttle()
        try:
            # 获取北向资金个股持仓
            df = ak.stock_hsgt_individual_em(stock=symbol)
            if df.empty: return {"symbol": symbol, "note": "非北向资金标的或无数据"}

            latest = df.iloc[-1]
            # 近20日净流入
            recent = df.tail(20)
            net_flow_20d = _safe(round(float(recent['净买入'].sum()) / 1e8, 2)) if '净买入' in recent.columns else None

            return {
                "symbol": symbol,
                "latest_date": str(latest.get('日期', '')),
                "hold_shares_million": _safe(round(float(latest.get('持股数量', 0)) / 1e4, 2)),
                "hold_ratio_pct": _safe(round(float(latest.get('持股占比', 0)), 2)),
                "net_flow_20d_billion": net_flow_20d,
                "recent_trend": "增持" if net_flow_20d and net_flow_20d > 0 else ("减持" if net_flow_20d and net_flow_20d < 0 else "持平"),
                "source": "eastmoney",
            }
        except Exception as e:
            if attempt == 2: return {"error": str(e)[:100], "note": "北向资金数据获取失败，可能该股非沪深港通标的"}
            time.sleep(3)

# ── 工具 9: 筹码分布（East Money）─────────────────────

@mcp.tool()
def get_chip_distribution(symbol: str) -> dict:
    """
    获取筹码分布数据：获利盘比例、平均成本、筹码集中度（East Money源，带重试）

    Args:
        symbol: 股票代码
    """
    for attempt in range(3):
        _throttle()
        try:
            df = ak.stock_cyq_em(symbol=symbol)
            if df.empty: return {"error": f"No chip distribution data for {symbol}"}

            latest = df.iloc[-1]
            profit_ratio = _safe(round(float(latest.get('获利比例', latest.get('获利盘', 0))), 2))
            avg_cost = _safe(round(float(latest.get('平均成本', 0)), 2))

            # 筹码集中度：近几期获利比例标准差，越小越集中
            if '获利比例' in df.columns:
                concentration = _safe(round(float(df['获利比例'].tail(10).std()), 2))
            elif '获利盘' in df.columns:
                concentration = _safe(round(float(df['获利盘'].tail(10).std()), 2))
            else:
                concentration = None

            return {
                "symbol": symbol,
                "latest_date": str(latest.get('日期', df.index[-1] if hasattr(df.index, '__getitem__') else '')),
                "profit_ratio_pct": profit_ratio,
                "avg_cost": avg_cost,
                "concentration_index": concentration,
                "interpretation": (
                    "低位密集" if profit_ratio and profit_ratio < 30 else
                    "中位分布" if profit_ratio and profit_ratio < 70 else
                    "高位密集" if profit_ratio else "N/A"
                ),
                "note": "concentration_index 越低筹码越集中，<5高集中，5-10中等，>10分散",
                "source": "eastmoney",
            }
        except Exception as e:
            if attempt == 2: return {"error": str(e)[:100]}
            time.sleep(3)

# ── Main ─────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
