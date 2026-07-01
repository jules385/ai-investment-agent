#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")


def parse_date(value: str | None) -> datetime:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=TZ)
    return datetime.now(TZ)


def daily_window(day: datetime) -> dict[str, str]:
    start = datetime.combine(day.date() - timedelta(days=1), time(0, 0, 0), TZ)
    end = datetime.combine(day.date(), time(23, 59, 59), TZ)
    return {
        "date": day.strftime("%Y-%m-%d"),
        "window_start": start.strftime("%Y-%m-%d %H:%M:%S"),
        "window_end": end.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Shanghai",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the A-share daily report time window.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD. Defaults to today in Asia/Shanghai.")
    args = parser.parse_args()
    print(json.dumps(daily_window(parse_date(args.date)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
