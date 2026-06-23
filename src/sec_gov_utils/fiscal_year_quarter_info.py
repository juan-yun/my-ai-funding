import sys
sys.path.append(".")
from ai_lab_comm.log_util import log

import requests
from datetime import datetime, timedelta
from constants import USER_AGENT
from sec_gov_utils.corp_ticker_utils import SecGovCompanyTickerUtils
from sec_gov_utils.all_submission_cache  import AllSubmissionCache


def add_business_days(dt: datetime, days: int) -> datetime:
    """加 N 个工作日（跳过周末）"""
    current = dt
    count = 0
    while count < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return current

def add_months(dt: datetime, months: int) -> datetime:
    """安全加减月份"""
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, [31,28,31,30,31,30,31,31,30,31,30,31][month-1])
    return datetime(year, month, day)

def get_fiscal_year_end_from_sec(ticker: str) -> dict:
    """
    从 SEC 官方获取公司 Fiscal Year End (月/日)
    返回 {"month": 1, "day": 31}
    """
    headers = {
        "User-Agent": USER_AGENT,
    }

    corp_info = SecGovCompanyTickerUtils.get_corp_info(ticker)
    cik_str = str(corp_info.cik).zfill(10)

    info = AllSubmissionCache.download_one_submission(cik_str, ticker)

    fye = info["fiscalYearEnd"]  # 格式 MMDD
    month = int(fye[:2])
    day = int(fye[2:])
    ret = {"month": month, "day": day, "filing_category": info["category"]}
    log.info(f"{corp_info} fiscal year end is {month}-{day}，filing category is {info['category']}")
    return ret  

def get_sec_fiscal_info(ticker: str, fiscal_year: int, fiscal_quarter: int = None):
    fye = get_fiscal_year_end_from_sec(ticker)
    fy_month = fye["month"]
    fy_day = fye["day"]
    
    quarters = []
    for q in range(1, 5):
        # 财季结束日
        q_end = add_months(datetime(fiscal_year, fy_month, fy_day), -(4 - q) * 3)
        # 财季开始日
        q_start = add_months(q_end, -3) + timedelta(days=1)

        # 计算截止日
        quarters.append({
            "quarter": f"Q{q}",
            "start_date": q_start.date(),
            "end_date": q_end.date()})

    # 4. 返回单季度 或 全年
    for q in range(1,5):
        log.info(f"quarters[{q}] is {quarters[q-1]}")
    if fiscal_quarter is not None:
        if fiscal_quarter not in (1,2,3,4):
            raise ValueError("quarter must be 1-4")
        return quarters[fiscal_quarter - 1]
    return quarters

# ==============================
# 使用示例
# ==============================
if __name__ == "__main__":
    # 测试 全年 4 个季度
    log.info("\n=== 全年 ===")
    full = get_sec_fiscal_info("MSFT", 2026)
    for q in full:
        log.info(f"{q}, {q["quarter"]}: {q["start_date"]} ~ {q["end_date"]}")
    log.info(full[-1]["10K_due"])

    # 测试 NVDA 2025 财年 Q2
    ("=== 单季度 ===")
    q2 = get_sec_fiscal_info("MSFT", 2025, fiscal_quarter=2)
    for k, v in q2.items():
        log.info(f"{k}: {v}")
    