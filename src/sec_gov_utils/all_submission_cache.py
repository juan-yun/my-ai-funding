
import os
import json
import time
import requests
from pathlib import Path
from tqdm import tqdm 

import sys
sys.path.append(".")
from ai_lab_comm.log_util import log
from sec_gov_utils.corp_ticker_utils import SecGovCompanyTickerUtils
from constants import USER_AGENT

CACHE_DIR = "/ssd/datasets/edgar/submission/"
CACHE_EXPIRE_HOURS = 24 * 7  # 缓存7天（公司信息不会频繁变）
REQUEST_DELAY = 0.05  # 请求间隔（秒），越小越快，但越容易被封
MAX_RETRY = 3  # 失败重试次数

class AllSubmissionCache:
    @staticmethod 
    def download_one_submission(cik: int, ticker: str):
        cik_str = str(cik).zfill(10)
        cache_path = os.path.join(CACHE_DIR, f"CIK{cik_str}_{ticker}.json")

        # ===================== 缓存判断 =====================
        if os.path.exists(cache_path):
            log.info(f"cache file exists: {cache_path}")
            mtime = os.path.getmtime(cache_path)
            if time.time() - mtime < CACHE_EXPIRE_HOURS * 3600:
                log.info(f"cache hit for CIK:{cik} ticker {ticker}")
                return json.load(open(cache_path, "r", encoding="utf-8")) 
    
        url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
        headers = {"User-Agent": USER_AGENT}
        for retry in range(MAX_RETRY):
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                # 写入缓存
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data

            except Exception as e:
                if retry == MAX_RETRY - 1:
                    log.error(f"❌ CIK:{cik} ticker {ticker} download failed：{str(e)}")
                    return
                time.sleep(0.05)

    @staticmethod
    def download_all_submissions(all_corp_info: dict):
        corp_list = all_corp_info.values()
        log.info("start download all submissions...")
        current, total = 0, len(corp_list)
        for corp in tqdm(corp_list, desc="download progress"):
            log.info(f"now try to download submission info for {current}/{total}\n \
                       corp: {corp} ")
            current += 1
            AllSubmissionCache.download_one_submission(corp.cik, corp.ticker)
            time.sleep(REQUEST_DELAY)
        log.info("all submissions download/cache done!\n")

    @staticmethod
    def load_all_local_submissions() -> list:
        files = list(Path(CACHE_DIR).glob("CIK*.json"))
        result = {}

        log.info(f"files: {files}")
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fobj:
                    cik_str, ticker = os.path.basename(f).rstrip(".json").lstrip("CIK").split("_")
                    cik = int(cik_str)
                    result[cik] = json.load(fobj)
                    log.info(f"cik: {cik}, ticker: {ticker}")    
            except Exception as e:
                log.error(f"❌ load local submission cache failed: {f}, error: {str(e)}")    
                continue
        log.info(f"✅ 本地已加载 {len(result)} 家公司数据")
        return result

if __name__ == "__main__":
    all_infos = SecGovCompanyTickerUtils.fetch().all_info()
    AllSubmissionCache.download_all_submissions(all_infos)
    #ret = AllSubmissionCache.load_all_local_submissions()

    