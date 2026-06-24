# -*- coding: utf-8 -*-

'''
src.edgar_tools_facade.financial_metrics_api 的 Docstring
功能如下：
1. 能够访问financial.ai的get_financial_metrics接口，获取股票的财务指标
2. 能够通过调用edgar_tools_facade.py中的get_financial_metrics方法，获取股票的财务指标
3. 上述两个接口的参数和返回值格式相同，名称稍作区别
4. 提供一个测试类，能够对dev_log.md中的股票代码进行测试
'''

import pandas as pd
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from tabulate import tabulate
import sys
import os

sys.path.append(".")
from ai_lab_comm.log_util import log
from edgar_tools_facade import EdgarToolsFacade
from financial_datasets_ai_client import get_financial_metrics as get_financial_metrics
from data.models import FinancialMetrics
from price_util.us_stock_price_util import UsStockPriceUtil
from concept_mapping_constants import ALL_DEPENDENCY_CONCEPTS

class FinancialMetricsAPI:
    """
    Financial Metrics API class to access financial metrics from different sources
    """
    
    def __init__(self):
        self.edgar_tools = EdgarToolsFacade()
        self.price_tools = UsStockPriceUtil()   

    def get_price(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Access financial.ai's get_financial_metrics interface to get stock financial metrics
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            DataFrame containing the requested financial metrics
        """
        log.info(f"Getting price from AI for ticker {ticker}, start_date: {start_date}, end_date: {end_date}")
        return self.price_tools.get_stock_price_by_akshare(ticker, start_date, end_date)

    def get_financial_metrics_from_3rd_api(self, 
                                    ticker:  str, end_date: str, period: str = "annual",
                                    limit: int = 1):
        try:
            results = get_financial_metrics( ticker=ticker, end_date=end_date, period=period, limit=limit)
            return results
        except Exception as e:
            log.error(f"Error retrieving financial metrics from finanacial.ai API: {str(e)}")
            raise
    
    def get_financial_metrics_from_edgar(self, 
                                       tickers: List[str], 
                                       end_date: str,
                                       period: str = "annual",
                                       limit: int = 1) -> pd.DataFrame:
        """
        Get financial metrics by calling edgar_tools_facade's methods
        Args:
            tickers: List of stock ticker symbols
            metrics: List of financial metrics to retrieve
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            period: Period type ('annual' or 'quarterly')
            limit: Number of records to limit
        Returns:
            DataFrame containing the requested financial metrics
        """
        concepts = ALL_LINE_CONCEPTS
        log.info(f"Getting financial metrics from Edgar for tickers: {tickers}, metrics: {concepts}")
        try:
            results = []
            for ticker in tickers:
                result = self.edgar_tools.query_concepts(
                    ticker=ticker, line_concepts=concepts,
                    #start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                    end_date=datetime.strptime(end_date, '%Y-%m-%d'),
                    period=period,
                    limit=limit
                )
                results.append(result)
            combined_results = pd.DataFrame(results)
            log.info(f"Successfully retrieved financial metrics from Edgar")
            return combined_results
        except Exception as e:
            log.error(f"Error retrieving financial metrics from Edgar: {str(e)}")
            raise


class FinancialMetricsAPITest:
    """
    Test class to test the FinancialMetricsAPI with stock codes from dev_log.md
    """
    
    def __init__(self):
        """
        Initialize the test class
        """
        self.api = FinancialMetricsAPI()
    
        #行业领域    免费访问的股票代码 (Ticker)                         公司名称
        #科技与通信  AAPL、MSFT、AMZN、CRM、CSCO、INTC、IBM             苹果、微软、亚马逊、赛富时、思科、英特尔、IBM
        #金融与服务  V、AXP、GS、JPM、TRV                               维萨、美国运通、高盛、摩根大通、旅行者保险
        #消费与零售  WMT、HD、NKE、DIS、MCD、KO、PG                      沃尔玛、家得宝、耐克、迪士尼、麦当劳、可口可乐、宝洁
        #医疗与健康  UNH、JNJ、MRK、AMGN                                联合健康、强生、默沙东、安进
        #工业与能源 BA、CAT、HON、MMM、CVX                               波音、卡特彼勒、霍尼韦尔、3M、雪佛龙
        self.tickers = {
            #"high_tech": {"AAPL": "苹果", "MSFT": "亚马逊", "CRM": "赛富时", "CSCO": "思科", "INTC": "英特尔", "IBM": "IBM"} ,
            #"financial_services": {"V": "维萨", "AXP": "美国运通", "GS": "高盛", "JPM": "摩根大通", "TRV": "旅行者保险"},
            #"retail": {"WMT": "沃尔玛", "HD": "家得宝", "NKE": "耐克", "DIS": "迪士尼", "MCD": "麦当劳", "KO": "可口可乐", "PG": "宝洁"},
            #"healthcare": {"UNH": "联合健康", "JNJ": "强生", "MRK": "默沙东", "AMGN": "安进"},
            "industrial": {"BA": "波音", "CAT": "卡特彼勒", "HON": "霍尼韦尔", "MMM": "3M", "CVX": "雪佛龙"}
        }

    def test_financial_ai_interface(self,
                         tickers: Optional[List[str]] = None, 
                         end_date: str = "2026-12-31",
                         period: str = "annual", limit: int = 3) -> pd.DataFrame:
        key = f"tickers: {tickers}, end_date: {end_date}, period: {period}, limit: {limit}"
        total_result = {}
        for ticker in tickers:
            log.info(f"Testing AI interface for ticker: {ticker}, end_date: {end_date}, period: {period}, limit: {limit}")
            try:
                result = self.api.get_financial_metrics_from_3rd_api(
                    ticker=ticker,
                    end_date=end_date,
                    period=period, limit=limit,
                )
                log.info("Edgar interface test completed successfully")
                total_result[key] = result
            except Exception as e:
                log.error(f"Edgar interface test failed: {str(e)}")
                continue
        return total_result

    def test_edgar_interface(self,
                            tickers: Optional[List[str]] = None,
                            end_date: str = "2026-12-31",
                            period: str = "annual", limit: int = 3) -> pd.DataFrame:
        try:
            result = self.api.get_financial_metrics_from_edgar(
                tickers=tickers,
                end_date=end_date,
                period=period, limit=limit,
            )
            log.info("Edgar interface test completed successfully")
            return result
        except Exception as e:
            log.error(f"Edgar interface test failed: {str(e)}")
            raise

    
    def show_table(self, data: Dict[str, Dict[str, Any]]):
        log.info("now show table for result********************************")
        if len(data) == 0:
            log.error("no data to show")
            return
        for key, (cache_dict_str, objs) in data.items():
            log.error(f"{key} {cache_dict_str} {type(objs)}")
            headers = ["Field"] + [f"report_period:{getattr(obj, "report_period")}" for obj in objs]
            rows = []
            for field in FinancialMetrics.model_fields:
                if field == "report_period": continue
                rows.append([field] + [getattr(fin_metrics_obj, field) for fin_metrics_obj in objs])
        log.error(tabulate(rows, headers=headers, tablefmt="fancy_grid"))        

    
    def run_comprehensive_test(self, tickers: Optional[List[str]] = None, 
                               end_date: str = "2026-12-31", period: str = "annual", limit: int = 3) \
                               -> Dict[str, pd.DataFrame]:
        log.info("Running comprehensive tests on both interfaces")
        
        results = {}
        log.info(f"now try to test tickers: {tickers}")
        # Test AI interface
        try:
            results['ai_interface'] = self.test_financial_ai_interface(
                tickers=tickers,
                end_date=end_date,
                period=period,
                limit=limit 
            )
        except Exception as e:
            log.error(f"AI interface test failed: {str(e)}")
            results['ai_interface'] = None

        self.show_table(results['ai_interface'])
        
        # Test Edgar interface
        #try:
        #    results['edgar_interface'] = self.test_edgar_interface(
        #        tickers=tickers,
        #        metrics=metrics,
        #        end_date=end_date
        #    )
        #except Exception as e:
        #    log.error(f"Edgar interface test failed: {str(e)}")
        #    results['edgar_interface'] = None
        
        #log.info("Comprehensive tests completed")
        return results


if __name__ == "__main__":
    corp_infos = {
        "tickers": ["AAPL"],
        "end_date": "2026-06-31", 
        "period": "annual", "limit": 1,
    }
 
    tickers = ["AAPL"] #, "TSLA", "MSFT", "NVDA"]
    test = FinancialMetricsAPITest()
    test.run_comprehensive_test(**corp_infos)