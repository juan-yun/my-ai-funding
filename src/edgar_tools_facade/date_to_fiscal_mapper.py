import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date

import sys
sys.path.append(".")
from sec_gov_utils.fiscal_year_quarter_info import get_sec_fiscal_info
from ai_lab_comm.log_util import log

class DateToFiscalMapper:
    """
    将日期范围映射到财政年度/季度的工具类
    """
    
    def __init__(self):
        self.log = log
    
    def convert_single_date_to_fiscal_period(self, 
                                           company_ticker: str, 
                                           target_date: str, 
                                           period: str = "annual") -> Optional[Dict[str, Any]]:
        """
        将单个日期转换为财政期间信息
        
        Args:
            company_ticker: 公司股票代码
            target_date: 目标日期 (格式: 'YYYY-MM-DD')
            period: 期间类型 ('annual' 或 'quarterly')
            
        Returns:
            财政期间信息字典
        """
        try:
            target_dt = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            # 获取公司的财政信息
            fiscal_info = get_sec_fiscal_info(company_ticker, target_date, target_date, period)
            
            if not fiscal_info or len(fiscal_info) == 0:
                self.log.warning(f"无法获取公司 {company_ticker} 在日期 {target_date} 的财政信息")
                return None
            
            # 找到最接近目标日期的财政期间
            closest_period = None
            min_diff = float('inf')
            
            for period_info in fiscal_info:
                period_start = datetime.strptime(period_info['start_date'], '%Y-%m-%d').date()
                period_end = datetime.strptime(period_info['end_date'], '%Y-%m-%d').date()
                
                # 检查目标日期是否在该财政期间内
                if period_start <= target_dt <= period_end:
                    closest_period = period_info
                    break
                else:
                    # 计算距离最近的财政期间
                    diff_to_start = abs((target_dt - period_start).days)
                    diff_to_end = abs((target_dt - period_end).days)
                    min_curr_diff = min(diff_to_start, diff_to_end)
                    
                    if min_curr_diff < min_diff:
                        min_diff = min_curr_diff
                        closest_period = period_info
            
            if closest_period:
                return {
                    'company_ticker': company_ticker,
                    'target_date': target_date,
                    'fiscal_year': closest_period['fiscal_year'],
                    'fiscal_quarter': closest_period.get('fiscal_quarter'),
                    'calendar_start_date': closest_period['start_date'],
                    'calendar_end_date': closest_period['end_date'],
                    'fiscal_period_type': period,
                    'overlap_days': self._calculate_overlap_with_target(
                        target_dt, 
                        datetime.strptime(closest_period['start_date'], '%Y-%m-%d').date(),
                        datetime.strptime(closest_period['end_date'], '%Y-%m-%d').date()
                    )
                }
            
            return None
            
        except Exception as e:
            self.log.error(f"转换单个日期到财政期间时出错: {str(e)}")
            return None
    
    def convert_date_range_to_fiscal_periods(self, 
                                           company_ticker: str, 
                                           start_date: str, 
                                           end_date: str, 
                                           period: str = "annual") -> List[Dict[str, Any]]:
        """
        将日期范围转换为财政期间列表
        
        Args:
            company_ticker: 公司股票代码
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            period: 期间类型 ('annual' 或 'quarterly')
            
        Returns:
            财政期间列表
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 获取公司在指定日期范围内的财政信息
            fiscal_info = get_sec_fiscal_info(company_ticker, start_date, end_date, period)
            
            if not fiscal_info:
                self.log.warning(f"无法获取公司 {company_ticker} 在日期范围 {start_date} 到 {end_date} 的财政信息")
                return []
            
            result = []
            for period_info in fiscal_info:
                fiscal_start = datetime.strptime(period_info['start_date'], '%Y-%m-%d').date()
                fiscal_end = datetime.strptime(period_info['end_date'], '%Y-%m-%d').date()
                
                # 计算与目标日期范围的交集
                overlap_start = max(start_dt, fiscal_start)
                overlap_end = min(end_dt, fiscal_end)
                
                if overlap_start <= overlap_end:  # 确保有交集
                    overlap_days = (overlap_end - overlap_start).days + 1
                    
                    result.append({
                        'company_ticker': company_ticker,
                        'fiscal_year': period_info['fiscal_year'],
                        'fiscal_quarter': period_info.get('fiscal_quarter'),
                        'calendar_start_date': period_info['start_date'],
                        'calendar_end_date': period_info['end_date'],
                        'overlap_start_date': overlap_start.strftime('%Y-%m-%d'),
                        'overlap_end_date': overlap_end.strftime('%Y-%m-%d'),
                        'overlap_days': overlap_days,
                        'fiscal_period_type': period,
                        'original_requested_start': start_date,
                        'original_requested_end': end_date
                    })
            
            # 按财政年度和季度排序
            result.sort(key=lambda x: (
                x['fiscal_year'], 
                x.get('fiscal_quarter', 0) or 0
            ))
            
            return result
            
        except Exception as e:
            self.log.error(f"转换日期范围到财政期间时出错: {str(e)}")
            return []
    
    def _calculate_overlap_with_target(self, 
                                     target_date: date, 
                                     fiscal_start: date, 
                                     fiscal_end: date) -> int:
        """
        计算目标日期与财政期间的重叠天数（始终为1，因为是单个日期）
        """
        if fiscal_start <= target_date <= fiscal_end:
            return 1
        return 0

def convert_single_date_to_fiscal_period(company_ticker: str, 
                                       target_date: str, 
                                       period: str = "annual") -> Optional[Dict[str, Any]]:
    """
    将单个日期转换为财政期间信息（便捷函数）
    
    Args:
        company_ticker: 公司股票代码
        target_date: 目标日期 (格式: 'YYYY-MM-DD')
        period: 期间类型 ('annual' 或 'quarterly')
        
    Returns:
        财政期间信息字典
    """
    mapper = DateToFiscalMapper()
    return mapper.convert_single_date_to_fiscal_period(company_ticker, target_date, period)

def convert_date_range_to_fiscal_periods(company_ticker: str, 
                                       start_date: str, 
                                       end_date: str, 
                                       period: str = "annual") -> List[Dict[str, Any]]:
    """
    将日期范围转换为财政期间列表（便捷函数）
    
    Args:
        company_ticker: 公司股票代码
        start_date: 开始日期 (格式: 'YYYY-MM-DD')
        end_date: 结束日期 (格式: 'YYYY-MM-DD')
        period: 期间类型 ('annual' 或 'quarterly')
        
    Returns:
        财政期间列表
    """
    mapper = DateToFiscalMapper()
    return mapper.convert_date_range_to_fiscal_periods(company_ticker, start_date, end_date, period)

def test_date_fiscal_mapping():
    """
    测试日期到财政期间的映射功能
    """
    mapper = DateToFiscalMapper()
    
    # 测试单个日期转换
    print("测试单个日期转换:")
    single_result = mapper.convert_single_date_to_fiscal_period("NVDA", "2026-02-15", "annual")
    if single_result:
        print(f"  日期 2026-02-15 映射到财政期间: {single_result}")
    else:
        print("  未找到对应的财政期间")
    
    # 测试日期范围转换
    print("\n测试日期范围转换:")
    range_result = mapper.convert_date_range_to_fiscal_periods("NVDA", "2025-01-01", "2026-03-31", "annual")
    print(f"  日期范围 2025-01-01 到 2026-03-31 映射到 {len(range_result)} 个财政期间:")
    for i, period in enumerate(range_result):
        print(f"    {i+1}. 财政年度: {period['fiscal_year']}, "
              f"开始: {period['calendar_start_date']}, "
              f"结束: {period['calendar_end_date']}, "
              f"重叠天数: {period['overlap_days']}")
    
    # 测试季度数据
    print("\n测试季度数据:")
    quarterly_result = mapper.convert_date_range_to_fiscal_periods("NVDA", "2025-01-01", "2025-12-31", "quarterly")
    print(f"  2025年季度数据: {len(quarterly_result)} 个期间")
    for i, period in enumerate(quarterly_result):
        print(f"    {i+1}. 财政年度: {period['fiscal_year']}, "
              f"季度: {period['fiscal_quarter']}, "
              f"日历开始: {period['calendar_start_date']}, "
              f"日历结束: {period['calendar_end_date']}")

if __name__ == "__main__":
    test_date_fiscal_mapping()
