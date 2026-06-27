import akshare as ak
import pandas as pd
import numpy as np
import sys

sys.path.append("./")
from ai_lab_comm.log_util import log

class UsStockPriceUtil:
    OHLCV = ["date", "open", "high", "low", "close", "volume"]
    def __init__(self):
        pass

    @classmethod
    def query(cls, symbol, adjust, start_date=None, end_date=None):
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)

        df = ak.stock_us_daily(symbol=symbol, adjust=adjust)
        if None is df:
            log.error(f"get {symbol} price failed....")
            return None 
        if start_date is not None:
            df = df[df['date'] >= start_date]
        if end_date is not None:
            df = df[df['date'] <= end_date]
        filtered_df = df
        filtered_df = filtered_df.reset_index(drop=True)
        return filtered_df

    @classmethod
    def query_valid_close_price(cls, ticker, adjust, specific_date:str)->float|None:
        df = ak.stock_us_daily(symbol=ticker, adjust=adjust)
        log.info(f"latest price df: \n{df.head(10)}")
        if df is None:
            return None
        if specific_date is None or specific_date == "":
            return df.tail(1)["close"].iloc[0]
        price_df = df[df['date'] == specific_date]
        cnt = 0
        while cnt < 30:
            cnt += 1
            if price_df.empty:
                specific_date = pd.to_datetime(specific_date) - pd.Timedelta(days=1)
                price_df = df[df['date'] == specific_date]
            else:
                break
        if price_df.empty:
            return None
        price = price_df["close"].iloc[0]
        log.info(f"{ticker} price at {specific_date} is {price}")
        return price


    @classmethod
    def get_stock_price_by_akshare(cls, ticker, adjust, start_date, end_date):
        log.info(f"get {ticker} price by akshare, start_date is {start_date}, end_date is {end_date}")
        df = UsStockPriceUtil.query(symbol=ticker, adjust=adjust, start_date=start_date, end_date=end_date)
        if None is df:
            log.error(f"get {ticker} price failed....")
            return None
        for col in ["open", "close", "high", "low"]:
            df[col] = np.round(df[col], decimals=2)
        df.set_index(["date"], inplace=True, drop=False)
        return df[UsStockPriceUtil.OHLCV]
    
    
    @classmethod
    def compare_stock_price(cls, ticker, df1, df2):
        if df2 is None:
            log.warning(f"{ticker} df2 is None")
            log.info(f"df df1: \n{df1}")
            return None
        diff_df = df1.compare(df2)
        diff_df["volume_deviation"] = (df1["volume"] - df2["volume"])/df1["volume"]
        log.info(f"{ticker} compare result as  \n{diff_df}")
        return diff_df


if __name__ == '__main__':
    start_date = "2026-06-01"
    end_date = "2026-06-15"
    #for ticker in ["GOOGL", "AAPL", "MSFT", "TSLA", "NVDA"]:
    for ticker in ["AMZN"]:
        adjust=""
        df_actual = UsStockPriceUtil.get_stock_price_by_akshare(ticker, adjust,start_date, end_date)
        price1 = UsStockPriceUtil.query_valid_close_price(ticker, adjust, end_date)
        log.info(f"{ticker} price on {end_date} is {price1}")
        end_date = ""
        price2 = UsStockPriceUtil.query_valid_close_price(ticker, adjust, end_date)
        log.info(f"{ticker} price on {end_date} {price2}")
