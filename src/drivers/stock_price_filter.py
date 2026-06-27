import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_lab_comm.log_util import log
from financial_datasets_ai_client import get_prices
from price_util.us_stock_price_util import UsStockPriceUtil
from sec_gov_utils.corp_ticker_utils import SecGovCompanyTickerUtils
from sic_code_utils.sic_code_finder import get_sic_finder, CompanySICData
from edgar import *
from tabulate import tabulate


set_identity("juanyun2017@126.com")

@dataclass
class FilteredStock:
    """过滤后的股票数据"""
    ticker: str
    name: str
    price_min: float
    price_max: float
    price_avg: float
    sic_code: Optional[str]
    sic_industry: Optional[str]
    sic_sector: Optional[str]


class StockPriceFilter:
    """股票价格过滤器"""
    
    def __init__(self):
        self._sic_finder = get_sic_finder()
    
    def _get_all_tickers(self) -> List[str]:
        """获取所有可用的ticker列表"""
        all_ticker_infos = SecGovCompanyTickerUtils.fetch().all_info()
        tickers = list(all_ticker_infos.keys())
        #tickers  = ["AAPL", "MSFT", "ERIC", "NVDA", "MANU"]
        return tickers
    
    def _get_date_range(self, months: int = 1) -> Tuple[str, str]:
        """获取日期范围（默认最近1个月）"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30 * months)).strftime("%Y-%m-%d")
        return start_date, end_date
    
    def _get_price_range(self, ticker: str, start_date: str, end_date: str) -> Optional[Tuple[float, float, float]]:
        """获取股票在指定日期范围内的价格区间"""
        try:
            #adjust = "qfq-factor"
            adjust = ""
            prices = UsStockPriceUtil.get_stock_price_by_akshare(ticker=ticker, adjust=adjust, 
                                                                 start_date=start_date, end_date=end_date)
            if prices is None:
                log.warning(f"get {ticker} price failed.")
                return None
                
            close_prices = prices["close"].tolist()
            if not close_prices or len(close_prices) == 0:
                return None
            
            price_min = min(close_prices)
            price_max = max(close_prices)
            price_avg = sum(close_prices) / len(close_prices)
            
            return price_min, price_max, price_avg
        
        except Exception as e:
            log.error(f"get {ticker} price df failed: {e}")
            return None
    
    def filter_by_price_range(
        self,
        price_min: float,
        price_max: float,
        months: int = 1
    ) -> List[FilteredStock]:
        start_date, end_date = self._get_date_range(months)
        tickers = self._get_all_tickers()
        results = []
        
        log.info(f"begin filter: {start_date} to {end_date}, price range: [${price_min} - ${price_max}]")

        log.info(f"total stocks to check: {len(tickers)}")
        
        for i, ticker in enumerate(tickers):
            log.info(f"progress: {i}/{len(tickers)} - checking {ticker}")
            corp = Company(ticker)
            filings = corp.get_filings(form="10-K")
            if len(filings) == 0:
                log.warning(f"For company {ticker}, no filing found by edgar sdk.")
                continue

            price_data = self._get_price_range(ticker, start_date, end_date)
            if price_data is None:
                continue
            
            p_min, p_max, p_avg = price_data
            
            if price_min <= p_min and p_max <= price_max:
                sic_data = self._sic_finder.get_sic_by_ticker(ticker)
                
                stock = FilteredStock(
                    ticker=ticker,
                    name=sic_data.name if sic_data else "",
                    price_min=round(p_min, 2),
                    price_max=round(p_max, 2),
                    price_avg=round(p_avg, 2),
                    sic_code=sic_data.sic_code if sic_data else None,
                    sic_industry=sic_data.sic_industry if sic_data else None,
                    sic_sector=sic_data.sic_sector if sic_data else None
                )
                log.info(f"matched filter condition, stock: {stock}")
                results.append(stock)
        
        log.info(f"all done, filter stocks done, found {len(results)} stocks")
        return results
    
    def filter_by_price_range_with_sic(
        self,
        price_min: float,
        price_max: float,
        months: int = 1
    ) -> List[dict]:
        filtered_stocks = self.filter_by_price_range(price_min, price_max, months)
        
        results = []
        for stock in filtered_stocks:
            results.append({
                "ticker": stock.ticker,
                "name": stock.name,
                "price_range": f"${stock.price_min} - ${stock.price_max}",
                "average_price": f"${stock.price_avg}",
                "sic_code": stock.sic_code,
                "sic_industry": stock.sic_industry,
                "sic_sector": stock.sic_sector
            })
        
        return results


def main():
    """主函数 - 示例用法"""
    filter = StockPriceFilter()
    price_min, price_max = 0, 20
    # 示例：过滤最近1个月股价在$100-$200之间的股票
    filtered_stocks = filter.filter_by_price_range(price_min, price_max, months=1)
    
    log.info(f"matched filter condition, stock count: {len(filtered_stocks)}")
    header = ["Ticker", "Name", "Min_Price", "Price_Max", "Avg_Price", "SIC_Code", "Industry"]
    rows = []
    for stock in filtered_stocks:
        rows.append([
              stock.ticker,
              stock.name,
              stock.price_min,
              stock.price_max,
              stock.price_avg,
              stock.sic_code,
              stock.sic_industry])
    table = tabulate(rows, headers=header, tablefmt="grid")
    log.info("\n" + f"{table}")
    # 按行业分组统计
    log.info("\n\n按行业分布统计:")
    industry_counts = {}
    for stock in filtered_stocks:
        industry = stock.sic_industry or "Unknown_Industry"
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    for industry, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
        log.info(f"  {industry}: {count} stocks")


if __name__ == "__main__":
    main()