"""
SIC Code Finder - 行业代码查询工具

功能：
1. 获取所有公司的SIC代码
2. 将SIC映射为有意义的行业信息
3. 提供查询接口，基于ticker或者CIK查询SIC及其描述
4. 提供查询接口，基于SIC或者行业描述，查询公司信息
"""

import os
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel
import pandas as pd
import sys
from edgar import Company
sys.path.append("./")
from ai_lab_comm.log_util import log
from sec_gov_utils.corp_ticker_utils import SecGovCompanyTickerUtils



SIC_MAJOR_GROUPS = {
    "01": "农业生产",
    "02": "林业",
    "03": "渔业",
    "04": "狩猎和捕猎",
    "05": "矿业",
    "06": "金属矿",
    "07": "石油和天然气",
    "08": "建筑材料",
    "09": "其他采矿",
    "10": "金属冶炼",
    "11": "煤炭",
    "12": "天然气",
    "13": "石油",
    "14": "采矿服务",
    "15": "建筑施工",
    "16": "重型建筑",
    "17": "特种贸易",
    "20": "食品和饮料",
    "21": "烟草",
    "22": "纺织品",
    "23": "服装",
    "24": "木材产品",
    "25": "家具",
    "26": "纸张",
    "27": "印刷和出版",
    "28": "化学品",
    "29": "石油炼制",
    "30": "橡胶和塑料",
    "31": "皮革",
    "32": "石材、粘土和玻璃",
    "33": "初级金属",
    "34": "金属制品",
    "35": "工业机械",
    "36": "电子和电气设备",
    "37": "运输设备",
    "38": "仪器和相关产品",
    "39": "杂项制造",
    "40": "铁路运输",
    "41": "本地和郊区客运",
    "42": "卡车运输",
    "43": "美国邮政服务",
    "44": "水上运输",
    "45": "航空运输",
    "46": "管道运输",
    "47": "运输服务",
    "48": "通信",
    "49": "电力、天然气和卫生服务",
    "50": "批发贸易-耐用品",
    "51": "批发贸易-非耐用品",
    "52": "建筑材料和园林用品",
    "53": "综合百货商店",
    "54": "食品商店",
    "55": "汽车经销商和加油站",
    "56": "服装和配饰商店",
    "57": "家具和家庭用品商店",
    "58": "餐饮场所",
    "59": "杂项零售",
    "60": "存款机构",
    "61": "非存款信用机构",
    "62": "证券和商品经纪",
    "63": "保险 carriers",
    "64": "保险代理和经纪",
    "65": "房地产",
    "67": "控股公司",
    "70": "酒店和住宿",
    "72": "个人服务",
    "73": "商业服务",
    "75": "汽车修理",
    "76": "杂项修理",
    "78": "电影",
    "79": "娱乐和休闲",
    "80": "健康服务",
    "81": "法律服务",
    "82": "教育服务",
    "83": "社会服务",
    "84": "博物馆、植物园和动物园",
    "86": "会员组织",
    "87": "工程和管理服务",
    "88": "私人家庭服务",
    "89": "杂项专业服务",
    "91": "公共行政",
    "92": "司法和公共秩序",
    "93": "财政",
    "94": "教育",
    "95": "环境质量和住房",
    "96": "行政和支持",
    "97": "国际事务",
    "99": "非分类机构"
}

# SIC部门映射
SIC_SECTORS = {
    "A": {"name": "农业、林业和渔业", "codes": ["01", "02", "07", "08", "09"]},
    "B": {"name": "采矿", "codes": ["10", "12", "13", "14"]},
    "C": {"name": "建筑业", "codes": ["15", "16", "17"]},
    "D": {"name": "制造业", "codes": ["20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39"]},
    "E": {"name": "运输、通信、电力、燃气和卫生服务", "codes": ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49"]},
    "F": {"name": "批发贸易", "codes": ["50", "51"]},
    "G": {"name": "零售贸易", "codes": ["52", "53", "54", "55", "56", "57", "58", "59"]},
    "H": {"name": "金融、保险和房地产", "codes": ["60", "61", "62", "63", "64", "65", "67"]},
    "I": {"name": "服务业", "codes": ["70", "72", "73", "75", "76", "78", "79", "80", "81", "82", "83", "84", "86", "87", "88", "89"]},
    "J": {"name": "公共行政", "codes": ["91", "92", "93", "94", "95", "96", "97", "99"]}
}


@dataclass
class SICInfo:
    """SIC信息数据类"""
    sic_code: str
    sic_industry: str
    sic_sector: str
    sector_code: str


@dataclass
class CompanySICData:
    """公司SIC数据"""
    ticker: str
    name: str
    cik: Optional[str]
    sic_code: Optional[str]
    sic_industry: Optional[str]
    sic_sector: Optional[str]

@dataclass
class SICDescData:
    """SIC数据"""
    sic4_code: str
    sic4_desc: str
    ind_cd: str
    ind_desc: str
    maj_cd: str
    maj_desc: str
    div_desc: str
    div_cd: str

class SICCodeFinder:
    """SIC代码查询器"""
    
    def __init__(self):
        self._cached_sic_desc_dict: Dict[str, CompanySICData] = {}
        self._load_sic_data()


    def _load_sic_data(self):
        """加载SIC数据"""
        self._cached_sic_desc_dict = {}
        desc_file_path = os.path.join(os.path.dirname(__file__), "../../resource/osha_combined.csv")
        if not os.path.exists(desc_file_path):
            log.warning(f"SIC描述文件不存在: {desc_file_path}")
            return
        df = pd.read_csv(desc_file_path, sep=",")  
        
        for index, row in df.iterrows():
            key = str(row["SIC4_cd"])
            self._cached_sic_desc_dict[key] = SICDescData(
                sic4_code=row["SIC4_cd"],
                sic4_desc=row["SIC4_desc"],
                ind_cd=row["ind_cd"],
                ind_desc=row["ind_desc"],
                maj_cd=row["maj_cd"],
                maj_desc=row["maj_desc"],
                div_desc=row["div_desc"],
                div_cd=row["div_cd"]
            )

        log.info(f"load {len(self._cached_sic_desc_dict)} SIC descriptions from {desc_file_path}")

    def _fetch_all_companies(self) -> List[dict]:

        """获取所有公司列表"""
        log.info("Fetching all companies from API...")
        
        ret =  SecGovCompanyTickerUtils.fetch().all_info()
        return ret
    
    def get_sic_desc(self, sic_code: str) -> Optional[SICDescData]:
        new_code = sic_code.strip(".0")
        log.info(f"get_sic_desc: {new_code}")
        return self._cached_sic_desc_dict.get(new_code)
    
    def get_sic_info(self, sic_code: str) -> Optional[SICInfo]:
        """
        根据SIC代码获取行业信息
        
        Args:
            sic_code: SIC代码（如"3571"或"35"）
        
        Returns:
            SICInfo对象，包含行业和部门信息
        """
        if not sic_code:
            return None
        
        # 获取两位数字的主类别
        major_code = sic_code[:2]
        industry_name = SIC_MAJOR_GROUPS.get(major_code, "未知行业")
        
        # 确定部门
        sector_code = "未知"
        sector_name = "未知部门"
        for code, sector in SIC_SECTORS.items():
            if major_code in sector["codes"]:
                sector_code = code
                sector_name = sector["name"]
                break
        
        return SICInfo(
            sic_code=sic_code,
            sic_industry=industry_name,
            sic_sector=sector_name,
            sector_code=sector_code
        )
    
    def get_sic_by_ticker(self, ticker: str) -> Optional[CompanySICData]:
        ticker = ticker.upper().strip()
        company = Company(ticker) 
        if not company.is_company:
            log.warning(f"{ticker} is not a company")
            return None
        #desc = self.get_sic_desc(company.sic)
        result = CompanySICData(
            ticker=ticker,
            name=company.name,
            cik=company.cik,
            sic_code=company.sic,
            sic_industry=company.industry,
            sic_sector=""
        )
        return result
    
    def get_companies_by_sic(self, sic_code: str) -> List[CompanySICData]:
        sic_code = sic_code.strip()
        companies = self._fetch_all_companies()
        results = []
        
        for idx, ticker in enumerate(companies.keys()):
            log.info(f"try to filter {idx} {ticker}")
            company: CompanySICData = self.get_sic_by_ticker(ticker)
            if not company:
                continue
            if company.sic_code != sic_code:
                continue
            results.append(company)
            log.info(f"Get {len(results)} companies with sic_code {sic_code}")
        log.info(f"There are {len(results)} companies with sic_code {sic_code}") 
        return results
    
    def get_companies_by_industry(self, industry_keyword: str) -> List[CompanySICData]:
        """
        根据行业描述查询公司列表
        
        Args:
            industry_keyword: 行业关键词（如"软件"、"医疗"）
        
        Returns:
            符合条件的公司列表
        """
        industry_keyword = industry_keyword.lower().strip()
        companies = self._fetch_all_companies()
        results = []
        
        for company in companies:
            sic_industry = company.get('sic_industry', '').lower()
            sic_sector = company.get('sic_sector', '').lower()
            
            if industry_keyword in sic_industry or industry_keyword in sic_sector:
                result = CompanySICData(
                    ticker=company.get('ticker', ''),
                    name=company.get('name', ''),
                    cik=company.get('cik'),
                    sic_code=company.get('sic_code'),
                    sic_industry=company.get('sic_industry'),
                    sic_sector=company.get('sic_sector')
                )
                results.append(result)
        
        return results
    
    def get_all_sic_codes(self) -> List[Tuple[str, str]]:
        """
        获取所有SIC主类别代码及其描述
        
        Returns:
            SIC代码和描述的列表
        """
        return [(code, desc) for code, desc in SIC_MAJOR_GROUPS.items()]
    
    def get_all_sectors(self) -> Dict[str, str]:
        """
        获取所有部门信息
        
        Returns:
            部门代码到部门名称的映射
        """
        return {code: sector["name"] for code, sector in SIC_SECTORS.items()}
    

# 全局实例
_sic_finder = None

def get_sic_finder() -> SICCodeFinder:
    """获取全局SIC查询器实例"""
    global _sic_finder
    if _sic_finder is None:
        _sic_finder = SICCodeFinder()
    return _sic_finder


# 便捷函数
def get_sic_info_by_ticker(ticker: str) -> Optional[CompanySICData]:
    """根据ticker获取SIC信息（便捷函数）"""
    return get_sic_finder().get_sic_by_ticker(ticker)


def get_sic_info_by_cik(cik: str) -> Optional[CompanySICData]:
    """根据CIK获取SIC信息（便捷函数）"""
    return get_sic_finder().get_sic_by_cik(cik)

if __name__ == "__main__":
    finder = SICCodeFinder()
    print("=== 根据ticker查询 ===")
    ticker = "AAPL"
    corp_sic_info = finder.get_sic_by_ticker(ticker)
    if corp_sic_info:
        print(f"公司: {corp_sic_info.name} ({corp_sic_info.ticker})")
        print(f"SIC代码: {corp_sic_info.sic_code}")
        print(f"SIC行业: {corp_sic_info.sic_industry}")
        print(f"SIC部门: {corp_sic_info.sic_sector}")
        print(f"SIC描述: {finder.get_sic_desc(corp_sic_info.sic_code)}")

    # 2. 获取SIC详细信息

    print("\n=== SIC代码详细信息 ===")
    sic_info = finder.get_sic_info(corp_sic_info.sic_code)
    if sic_info:
        print(f"SIC代码: {sic_info.sic_code}")
        print(f"行业: {sic_info.sic_industry}")
        print(f"部门: {sic_info.sector_code} - {sic_info.sic_sector}")
    
    # 3. 根据SIC代码查询公司
    print("\n=== 根据SIC代码查询公司 ===")
    companies_at_this_sic = finder.get_companies_by_sic(corp_sic_info.sic_code)
    print(f"找到 {len(companies_at_this_sic)} 家相关公司")
    for company in companies_at_this_sic[:5]:
        print(f"  - {company.ticker}: {company.name}")
    
    # 4. 根据行业查询公司
    print("\n=== 根据行业查询公司 ===")
    tech_companies = finder.get_companies_by_industry("计算机")
    print(f"找到 {len(tech_companies)} 家科技公司")
    for company in tech_companies[:5]:
        print(f"  - {company.ticker}: {company.name} ({company.sic_industry})")
    
    # 5. 获取所有部门
    print("\n=== 所有部门 ===")
    sectors = finder.get_all_sectors()
    for code, name in sectors.items():
        print(f"  {code}: {name}")