import sys
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import re

sys.path.append(".")
from data.models import InsiderTrade
from ai_lab_comm.log_util import log
from edgar import Company, set_identity
from edgar import Filing
#from financial_ai_api import get_insider_trades as get_insider_trades_by_financial_ai_api

def build_insider_trade(ticker, filing: Filing) -> List[InsiderTrade]:
    form4 = filing.obj()
    #trades = form4.to_dataframe(include_metadata=True).to_dict(orient="records")
    summary = form4.get_ownership_summary()
    log.info(f"filing Form4 {filing.filing_date}")
    result = []
    director_positions = ["Director", "EVP", "CHIEF"]    
    for trans in summary.transactions:
        trade = InsiderTrade(
                ticker = ticker,
                transaction_type = trans.transaction_type,  
                issuer = summary.issuer_name,
                name = summary.insider_name,
                title = trans.description,
                is_board_director = any(pos in summary.position for pos in director_positions),
                transaction_date = summary.reporting_date,
                transaction_shares = trans.shares,
                transaction_price_per_share = trans.price_per_share,
                transaction_value = trans.value,
                shares_owned_before_transaction = None,
                shares_owned_after_transaction = summary.remaining_shares,
                security_title = trans.security_title,
                filing_date = filing.filing_date.strftime("%Y-%m-%d")
        )
        log.info(f"processed trade is: {trade}")
        result.append(trade)
    return result


def get_insider_trades_by_edgartools(ticker: str, end_date: str, start_date: str|None = None, limit: int = 1000) -> List[InsiderTrade]:
    set_identity("juanyun2017@126.com")
    if isinstance(start_date, str):
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = start_date
    if isinstance(end_date, str):
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = end_date
    company = Company(ticker)
    form4_filings = company.get_filings(form="4")
    total_trades = []
    for filing in form4_filings:
        filing_date = datetime.combine(filing.filing_date, datetime.min.time())
        if (start_dt and filing_date < start_dt) or (filing_date > end_dt):
            log.info(f"skipping filing at {filing_date} as it is outside date range [{start_dt} - {end_dt}]")
            continue
        try:
            total_trades.extend(build_insider_trade(ticker, filing))
            if len(total_trades) >= limit:
                log.info(f"reached limit {limit}, breaking")
                break
        except Exception as e:
            log.warning(f"Could not parse Form 4 filing for {ticker} filed on {filing.filing_date}: {str(e)}")
            continue
    return  total_trades[:limit]


def test_insider_trades_for_companies():
    """
    Test function to verify insider trades functionality for MSFT, NVDA, AAPL, TSLA, GOOGL
    """
    #companies = ["MSFT", "NVDA", "AAPL", "TSLA", "GOOGL"]
    companies = [ "MSFT"]
    start_date, end_date = "2024-03-12" , "2026-03-13"
    print("Testing insider trades for major companies...")
    
    for ticker in companies:
        print(f"\n--- Testing {ticker} ---")
        try:
            actual_trades = get_insider_trades_by_edgartools(ticker, end_date, start_date, limit=10)
            #expect_trades = get_insider_trades_by_financial_ai_api(ticker, end_date, start_date, limit=5)
            
            #print(f"Found {len(trades)} insider trades for {ticker}")
            
            #for i, trade in enumerate(trades):
            #    print(f"  Trade {i+1}: {trade.model_dump()}")
            #    
        except Exception as e:
            print(f"  Error getting insider trades for {ticker}: {str(e)}")


if __name__ == "__main__":
    test_insider_trades_for_companies()


'''
    {'ticker': 'MSFT', 
    'issuer': 'Microsoft Corp', 
    'name': 'Emma N Walmsley', 
    'title': None, 'is_board_director': True, 
    'transaction_date': '2026-03-12', 'transaction_type': 'Company grant or award', 
    'transaction_shares': 2.0, 'transaction_price_per_share': None, 
    'transaction_value': None, 'shares_owned_before_transaction': 1107.0, 
    'shares_owned_after_transaction': 1109.0, 
    'security_title': 'Restricted Stock Units', 'filing_date': '2026-03-13'}
    ''' 