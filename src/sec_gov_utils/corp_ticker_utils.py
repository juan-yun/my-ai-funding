import json
import requests
from requests import Response
import os
from datetime import datetime, timedelta

import sys
sys.path.append(".")
from constants import USER_AGENT
from ai_lab_comm.log_util import Log
log = Log(__name__).getlog()

class SingleCorpSumInfo():
    def __init__(self, cik, name, ticker, exchange):
        self.cik = int(cik)
        self.name = name
        self.ticker = ticker
        self.exchange = exchange 

    def __str__(self):
        return f"Ticker: {self.ticker}, Corp Name:{self.name}, CIK:{self.cik},  Exchange: {self.exchange}"


class AllCompanySummaryInfos():
    def __init__(self):
        self.infos = dict()

    def put(self, info: list):
        corp_info = SingleCorpSumInfo(
            info[0], info[1], info[2], info[3])
        key = f"{corp_info.ticker}"
        if key in self.infos.keys():
            log.error(f"Ticker:{corp_info.ticker}, CIK:{corp_info.cik}, Corp Name:{corp_info.name} has been existed.")
            return
        self.infos[key] =  corp_info

    def get(self, cik:str)->dict:
        if cik not in self.infos.keys():
            log.error(f"can not find any corp information with central index key as {cik} ")
            return None
        return self.infos.get(cik)

    def get_by_ticker(self, ticker:str)->SingleCorpSumInfo:
        if ticker in self.infos:
            return self.infos[ticker]
        return None

    def display(self):
        for _, corp_info in self.infos.items():
            log.info(f"{corp_info}") 
        log.info(f"There are {len(self.infos)} corp information currently.")
        return
    def all_info(self):
        return self.infos


class SecGovCompanyTickerUtils:
    CACHE_FILE_PATH = "../resource/company_tickers_exchange.json"
    CACHE_EXPIRY_DAYS = 1
    
    @staticmethod
    def _is_cache_expired(file_path: str) -> bool:
        """检查缓存文件是否过期"""
        if not os.path.exists(file_path):
            return True
        
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        expiry_time = file_modified_time + timedelta(days=SecGovCompanyTickerUtils.CACHE_EXPIRY_DAYS)
        
        return datetime.now() > expiry_time

    @staticmethod
    def _save_to_cache(data: dict, file_path: str):
        """保存数据到缓存文件"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 添加元数据，包括获取时间
        cache_data = {
            "last_updated": datetime.now().isoformat(),
            "data": data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
        log.info(f"Saved company ticker data to cache: {file_path}")

    @staticmethod
    def _load_from_cache(file_path: str) -> dict:
        """从缓存文件加载数据"""
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # 如果缓存结构包含元数据，则提取实际数据
            if isinstance(cached_data, dict) and "data" in cached_data:
                return cached_data["data"]
            else:
                # 兼容旧格式的缓存文件
                return cached_data
        except Exception as e:
            log.error(f"Error loading cache from {file_path}: {e}")
            return None
   
    @staticmethod
    def get_corp_info(ticker:str)->SingleCorpSumInfo:
        all_infos = SecGovCompanyTickerUtils.fetch().all_info()
        if ticker not in all_infos.keys():
            log.error(f"can not find any corp information with ticker as {ticker}")
            return None 
        return all_infos.get(ticker)

    @staticmethod
    def fetch():
        cache_file_path = SecGovCompanyTickerUtils.CACHE_FILE_PATH
        
        if not SecGovCompanyTickerUtils._is_cache_expired(cache_file_path):
            log.info("Loading company ticker data from cache...")
            cached_data = SecGovCompanyTickerUtils._load_from_cache(cache_file_path)
            
            if cached_data:
                data_list = cached_data["data"] if isinstance(cached_data, dict) and "data" in cached_data else cached_data
                log.info(f"Loaded {len(data_list)} corp information from cache.")
                
                all_infos = AllCompanySummaryInfos()
                for single_corp_data in data_list:
                    all_infos.put(single_corp_data)
                
                return all_infos
            else:
                log.warning("Cache exists but could not be loaded, fetching fresh data...")
        
        # 缓存不存在或已过期，从网络获取新数据
        log.info("Fetching fresh company ticker data from SEC...")
        url = 'https://www.sec.gov/files/company_tickers_exchange.json'

        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }

        resp:Response = requests.get(url=url, headers=headers)
        if resp.status_code != 200:
            log.error(f"request {url} failed, due to {resp}")
            # 如果网络请求失败，尝试使用过期的缓存
            cached_data = SecGovCompanyTickerUtils._load_from_cache(cache_file_path)
            if cached_data:
                log.warning("Using expired cache due to network failure...")
                data_list = cached_data["data"] if isinstance(cached_data, dict) and "data" in cached_data else cached_data
                all_infos = AllCompanySummaryInfos()
                for single_corp_data in data_list:
                    all_infos.put(single_corp_data)
                return all_infos
            return None
            
        data = resp.json() # Check the JSON Response Content documentation below
        data_list = data["data"]
        log.info(f"There are {len(data_list)} corp information.")
        
        # 保存到缓存
        SecGovCompanyTickerUtils._save_to_cache(data, cache_file_path)
        
        all_infos = AllCompanySummaryInfos()
        for single_corp_data in data_list:
            all_infos.put(single_corp_data)     
        return all_infos

if __name__ == "__main__":
    ret = SecGovCompanyTickerUtils.fetch()
    ret.display()