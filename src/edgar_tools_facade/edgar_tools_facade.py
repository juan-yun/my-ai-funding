import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict,List
sys.path.append(".")
from tabulate import tabulate

from ai_lab_comm.log_util import log
from sec_gov_utils.fiscal_year_quarter_info import get_sec_fiscal_info
from edgar import set_identity, Filing, get_filings
from edgar import *
from edgar.xbrl.statements  import Statement
#from financial_datasets_ai_client import search_line_items, query_all_financial_concepts
from financial_datasets_ai_client import query_all_financial_concepts, search_line_items
from src.edgar_tools_facade.concept_mapping_constants import EDGAR_TOOLS_LINE_ITEMS_MAP, ALL_DEPENDENCY_CONCEPTS
from src.edgar_tools_facade.concept_mapping_constants import ALL_CONCEPTS_ITEMS
from price_util.us_stock_price_util import UsStockPriceUtil

'''
EdgarTools Document https://edgartools.readthedocs.io/en/latest/
'''

class EdgarToolsFacade:
    def __init__(self):
        set_identity("juanyun2017@126.com")
        pd.set_option('display.max_rows', None)         # 显示所有行，不省略

        pd.set_option('display.max_columns', None)      # 显示所有列（可选，一起加上更舒服）

        pd.set_option('display.width', None)            # 列宽不限制（防止内容被截断）
        pd.set_option('display.max_colwidth', None)     # 列宽不限制（防止内容被截断）

    def query_concepts(self, ticker: str, line_concepts: List, 
                       end_date: datetime, period: str, limit: int = 1):
        result = {}
        target_line_concepts = line_concepts + \
            ALL_DEPENDENCY_CONCEPTS["income_statement"] + \
            ALL_DEPENDENCY_CONCEPTS["balance_sheet"] + \
            ALL_DEPENDENCY_CONCEPTS["cash_flow_statement"] 
        
        log.info(f"Try to query line concepts by edgar tools for corp {ticker}, end date{end_date}, \
                     {period}, {limit}")
        line_concepts_cfgs = {}
        for line_concept in target_line_concepts:
            if line_concept not in EDGAR_TOOLS_LINE_ITEMS_MAP:
                log.warning(f"line item {line_concept} not found in edgar tools line items map")
                continue
            line_item_config = EDGAR_TOOLS_LINE_ITEMS_MAP[line_concept]
            line_concepts_cfgs[line_concept] = line_item_config
            
        form_type = "10-K" if period == "annual" else "10-Q"
        company_obj, filings = self.filter_filing(ticker, period, form_type, end_date, limit)
        total_result = []
        for filing in filings:
            result = self.query_concepts_from_filing(company_obj, filing, period, line_concepts_cfgs)
            total_result.append(result)
        return total_result
    
    def query_concepts_from_filing(self, company_obj: Company, filing: Filing, period: str, line_items_cfgs: Dict):
        ticker = company_obj.get_ticker()
        result = {}
        result["ticker"] = ticker
        result["report_period"] = filing.period_of_report
        result["period"] = period
        result["currency"] = "USD"
        log.info(f"Filing for ticker {ticker} date is {filing.period_of_report}, url is {filing.url}")
        self.get_line_concepts_from_filing(ticker, filing, "income_statement", line_items_cfgs, result)
        self.get_line_concepts_from_filing(ticker, filing, "balance_sheet", line_items_cfgs, result)
        result["effective_tax_rate"] = self.query_effective_tax_rate(company_obj, filing, period)
        result["interest_expense"] = self.query_interest_expense(company_obj, filing, period)
        result["outstanding_shares"] = self.query_outstanding_shares(company_obj, filing, period)
        result["book_value_per_share"] = self._calc_book_value_per_share(result)
        self.get_line_concepts_from_filing(ticker, filing, "cash_flow_statement", line_items_cfgs, result)
        result["market_cap"] = self._calc_market_cap(ticker, result, filing.period_of_report)
        log.info(f"query result ALL is {result}")
        return result   

    def query_effective_tax_rate(self, company: Company, filing: Filing, period: str):
        log.info("begin query effective tax rate")
        facts = company.get_facts()
        gaap_values = facts.query()\
            .by_concept("us-gaap:EffectiveIncomeTaxRateContinuingOperations") \
            .by_fiscal_year(int(filing.report_date[:4]))\
            .by_form_type('10-K')\
            .sort_by('filing_date')\
            .execute()
        log.info(f"effective_tax_rate gaap_values is {gaap_values}")
        if len(gaap_values) <= 0:
            log.warning(f"For company {company.get_ticker()}, period {period}, no effective tax rate found")
            return 0.0
        gaap_values = gaap_values[-1].numeric_value
        if gaap_values is not None:
            log.info(f"For company {company.get_ticker()},  period {period}, effective tax rate gaap_value is {gaap_values}")
            return gaap_values
        return 0.0


    def query_interest_expense(self, company: Company, filing: Filing, period: str):
        facts = company.get_facts()
        gaap_values = facts.query()\
            .by_concept("us-gaap:InterestExpense") \
            .by_fiscal_year(int(filing.report_date[:4]))\
            .by_form_type('10-K')\
            .sort_by('filing_date')\
            .execute()
        log.info(f"gaap_values is {gaap_values}")
        if len(gaap_values) <= 0:
            log.warning(f"For company {company.get_ticker()}, period {period}, no interest expense found")
            return 0.0
        gaap_values = gaap_values[-1].numeric_value
        if gaap_values is not None:
            log.info(f"For company {company.get_ticker()},  period {period}, interest expense gaap_value is {gaap_values}")
            return gaap_values
        return 0.0


    def query_outstanding_shares(self, company: Company, filing: Filing, period: str):
        facts = company.get_facts() #period_type="annual")
        dei_results = facts.query()\
            .by_fiscal_year(int(filing.report_date[:4]))\
            .by_form_type('10-K')\
            .by_concept("dei:EntityCommonStockSharesOutstanding")\
            .sort_by('filing_date')\
            .execute()
        
        dei_value = dei_results[0].numeric_value if len(dei_results) >0 else None
        if dei_value is not None:
            log.info(f"For {company.get_ticker()}, period {period}, dei_value is {dei_value}")
            return dei_value
        gaap_value = facts.query()\
            .by_concept('us-gaap:CommonStockSharesOutstanding')\
            .by_fiscal_year(int(filing.report_date[:4]))\
            .by_form_type('10-K')\
            .sort_by('filing_date')\
            .execute()
        gaap_value = gaap_value[0].numeric_value if len(gaap_value) >0 else None
        if gaap_value is not None:
            log.info(f"For company {company.get_ticker()}, period {period}, gaap_value is {gaap_value}")
            return gaap_value
        log.warning(f"For {company.get_ticker()}, period {period}, no outstanding shares found")

        gaap_value = facts.query()\
            .by_concept('us-gaap:CommonStockSharesOutstanding')\
            .by_fiscal_year(int(filing.report_date[:4]))\
            .by_form_type('10-K')\
            .sort_by('filing_date')\
            .execute()
 

        return 0.0

    def display_query_concepts_results(self, total_result:Dict):
        for access_number, result in total_result.items():
            log.info(f"access_number is {access_number}")
            log.info(f"result is ")
            for line_item, value in result.items():
                log.info(f"{line_item} is {value}") 

    def filter_filing(self, ticker:str, period: str, form_type: str,
                      end_date: datetime, limit)->Filing:
        company_obj = Company(ticker)
        log.info(f"Shares Outstanding are: {company_obj.shares_outstanding:,.0f}")
        filings = company_obj.get_filings(form=form_type)
        filter_filings = []
        cnt = 0
        for filing in filings:
            filing_date = datetime.combine(filing.filing_date, datetime.min.time())
            # filing.save(f"../filings/{ticker}_{filing_date}.html")
            log.info(f"filing_date is {filing_date}, type is {type(filing_date)}")
            log.info(f"end_date is {end_date}, type is {type(end_date)}")
            if filing_date <= end_date:
                filter_filings.append(filing)
                log.info(f"filter filing {filing_date}")
                cnt += 1
                if cnt >= limit:
                    break
        return company_obj, filter_filings


    def get_line_concepts_from_filing(self, ticker: str, filing: Filing, statement_type: str, line_concepts_cfgs: Dict,
                                      tmp_result:Dict[str, float]):
        xbrl = filing.xbrl()
        statements = xbrl.statements 
        if statement_type == "income_statement":
            income_statement = statements.income_statement()
            cfgs = {concept:cfg for concept, cfg in line_concepts_cfgs.items() if cfg["stmt"] == "IS"}
            self.extract_item_from_statement(ticker, income_statement, statement_type, cfgs,
                                                          tmp_result)
            tmp_result["gross_profit"] = self._calc_gross_profit(tmp_result)
            tmp_result["gross_margin"] = self._calc_gross_margin(tmp_result)
            tmp_result["operating_expense"] = self._calc_operating_expense(tmp_result)
            tmp_result["operating_margin"] = self._calc_operating_margin(tmp_result)
            tmp_result["ebit"] = self._calc_ebit(tmp_result)
            return
        if statement_type == "balance_sheet":
            balance_sheet = statements.balance_sheet()
            cfgs = {concept:cfg for concept, cfg in line_concepts_cfgs.items() if cfg["stmt"] == "BS"}
            self.extract_item_from_statement(ticker, balance_sheet, statement_type, cfgs, tmp_result)
            tmp_result["goodwill_and_intangible_assets"] = self._calc_goodwill_and_intangible_assets(tmp_result)
            tmp_result["working_capital"] = self._calc_working_capital(tmp_result)
            tmp_result["total_debt"] = self._calc_total_debt(tmp_result)
            tmp_result["debt_to_equity"] = self._calc_debt_to_equity(tmp_result)
            return
        if statement_type == "cash_flow_statement":
            cash_flow_statement = statements.cash_flow_statement()
            cfgs = {concept:cfg for concept, cfg in line_concepts_cfgs.items() if cfg["stmt"] == "CF"}
            self.extract_item_from_statement(ticker, cash_flow_statement, statement_type, cfgs, tmp_result)
            tmp_result["return_on_invested_capital"] = self._calc_return_on_invested_capital(tmp_result)
            tmp_result["free_cash_flow"] = self._calc_free_cash_flow(tmp_result)
            tmp_result["issuance_or_purchase_of_equity_shares"] = self._calc_issuance_or_purchase_of_equity_shares(tmp_result)    
            tmp_result["ebitda"] = self._calc_ebitda(tmp_result)
            return

        return
    
    def _calc_market_cap(self, ticker, item_values: Dict, specific_date: str):
        ret = 0.0
        price = UsStockPriceUtil.query_valid_close_price(ticker, "", specific_date)
        if price is None:
            log.warning(f"get {ticker} price failed, specific_date is {specific_date}")
            return ret
        if "outstanding_shares" in item_values and item_values["outstanding_shares"] is not None:
            ret = price * item_values["outstanding_shares"]
        log.info(f"{ticker} market_cap is {price} * {item_values['outstanding_shares']} = {ret}")
        return ret

    def _calc_book_value_per_share(self, item_values: Dict):
        ret = 0.0
        shareholders_equity, outstanding_shares = 0.0, 0.0
        if "shareholders_equity" in item_values and item_values["shareholders_equity"] is not None:
            shareholders_equity = item_values["shareholders_equity"]
        if "outstanding_shares" in item_values and item_values["outstanding_shares"] is not None:
            outstanding_shares = item_values["outstanding_shares"]
        ret = shareholders_equity / outstanding_shares
        log.info(f"book_value_per_share is {shareholders_equity}/{outstanding_shares}={ret}")
        return ret

    def _calc_issuance_or_purchase_of_equity_shares(self, item_values: Dict):
        ret = 0.0
        proceed, payment_repurchase, payment_related_to_tax_withholding = 0.0, 0.0, 0.0
        if "proceeds_from_issuance_of_common_stock" in item_values and item_values["proceeds_from_issuance_of_common_stock"] is not None:
            proceed = item_values["proceeds_from_issuance_of_common_stock"]
        if "payment_for_repurchase_of_common_stock" in item_values and item_values["payment_for_repurchase_of_common_stock"] is not None:
            payment_repurchase = item_values["payment_for_repurchase_of_common_stock"]
        if "payment_related_to_tax_withholding_for_share_based_compensation" in item_values and item_values["payment_related_to_tax_withholding_for_share_based_compensation"] is not None:
            payment_related_to_tax_withholding = item_values["payment_related_to_tax_withholding_for_share_based_compensation"]
        ret = proceed + payment_repurchase + payment_related_to_tax_withholding
        log.info(f"Calculate issuance_or_purchase_of_equity_shares is {proceed} + {payment_repurchase} + {payment_related_to_tax_withholding} = {ret}")
        return ret
    
    def _calc_free_cash_flow(self, item_values: Dict):
        ret = 0.0
        operating_cash_flow, capital_expenditure = 0.0, 0.0
        if "operating_cash_flow" in item_values and item_values["operating_cash_flow"] is not None:
            operating_cash_flow = item_values["operating_cash_flow"]
        if "capital_expenditure" in item_values and item_values["capital_expenditure"] is not None:
            capital_expenditure = item_values["capital_expenditure"]
        ret = operating_cash_flow - abs(capital_expenditure)  #capital_expenditure is negative, so plus it
        log.info(f"calculate free cash flow, OCF is {operating_cash_flow}, CapEx is {capital_expenditure}, ret is {ret}")
        return ret

    def _calc_debt_to_equity(self, item_values: Dict):
        ret = 0.0
        total_liabilities, shareholders_equity = 0.0, 0.0
        if "total_liabilities" in item_values and item_values["total_liabilities"] is not None :
            total_liabilities = item_values["total_liabilities"]
        if "shareholders_equity" in item_values and item_values["shareholders_equity"] is not None:
            shareholders_equity = item_values["shareholders_equity"]
        ret = total_liabilities / shareholders_equity   
        return ret
    
    def _calc_return_on_invested_capital(self, item_values: Dict):
        ret = 0.0

        #net_income, dividends_and_other_cash_distributions, \
        ebit, effective_tax_rate, total_debt, shareholders_equity = 0.0, 0.0, 0.0, 0.0
        #if "net_income" in item_values and item_values["net_income"] is not None:
        #    net_income = item_values["net_income"]
        #if "dividends_and_other_cash_distributions" in item_values and item_values["dividends_and_other_cash_distributions"] is not None:
        #    dividends_and_other_cash_distributions = item_values["dividends_and_other_cash_distributions"]
        if "ebit" in item_values and item_values["ebit"] is not None:
            ebit = item_values["ebit"]

        if "effective_tax_rate" in item_values and item_values["effective_tax_rate"] is None:
            effective_tax_rate =  item_values["effective_tax_rate"]
        if "total_debt" in item_values and item_values["total_debt"] is not None:
            total_debt = item_values["total_debt"]
        if "shareholders_equity" in item_values and item_values["shareholders_equity"] is not None:
            shareholders_equity = item_values["shareholders_equity"]    
        invested_capital = total_debt + shareholders_equity
        nopat = ebit * (1 - effective_tax_rate)
        ret = nopat / invested_capital
        log.info(f"invested_capital is {invested_capital}, ebit is {ebit}")
        log.info(f"effective_tax_rate is {effective_tax_rate}, nopat is {nopat}")
        log.info(f"invested_capital is {invested_capital}={total_debt} + {shareholders_equity}")
        log.info(f"so calculate return_on_invested_capital is {nopat}/{invested_capital}={ret}")
        return ret

    def _calc_total_debt(self, item_values: Dict):
        ret = 0.0
        commercial_paper, short_term_debt, long_term_debt_current, long_term_debt_noncurrent = 0.0, 0.0, 0.0, 0.0
        operating_lease_noncurrent = 0.0
        operating_lease_noncurrent = 0.0
        if "commercial_paper" in item_values and item_values["commercial_paper"] is not None:
            commercial_paper = item_values["commercial_paper"]
        if "short_term_debt" in item_values and item_values["short_term_debt"] is not None:
            short_term_debt = item_values["short_term_debt"]
        if "long_term_debt_current" in item_values and item_values["long_term_debt_current"] is not None:
            long_term_debt_current = item_values["long_term_debt_current"]
        if "long_term_debt_noncurrent" in item_values and item_values["long_term_debt_noncurrent"] is not None:
            long_term_debt_noncurrent = item_values["long_term_debt_noncurrent"]
        if "operating_lease_noncurrent" in item_values and item_values["operating_lease_noncurrent"] is not None:
            operating_lease_noncurrent = item_values["operating_lease_noncurrent"] 
        ret = short_term_debt + long_term_debt_current + long_term_debt_noncurrent + operating_lease_noncurrent
        log.info(f"to calculate total_debt, commercial_paper: {commercial_paper}, short_term_debt: {short_term_debt}, long_term_debt_current: {long_term_debt_current}, long_term_debt_noncurrent: {long_term_debt_noncurrent}, \
                 operating_lease_noncurrent: {operating_lease_noncurrent},  \
                 ret: {ret}")
        return ret

    def _calc_working_capital(self, item_values: Dict):
        ret = 0
        if "current_assets" not in item_values or "current_liabilities" not in item_values:
            log.warning(f"current_assets or current_liabilities not in item_values, skip {item_values}")
            return ret  
        working_capital = item_values["current_assets"] - item_values["current_liabilities"]
        return working_capital
    
    def _calc_goodwill_and_intangible_assets(self, item_values: Dict):
        ret = 0
        if "goodwill" not in item_values and "intangible_assets" not in item_values:
            log.info(f"goodwill or intangible_assets not in item_values, skip goodwill_and_intangible_assets")
            return ret  
        good_will = 0.0 if item_values["goodwill"] is None else item_values["goodwill"]
        intangible_assets = 0.0 if item_values["intangible_assets"] is None else item_values["intangible_assets"]
        ret = good_will + intangible_assets
        return ret  
        
    def _calc_gross_profit(self, item_values: Dict):
        ret = None
        if "revenue" not in item_values or "cost_of_goods_sold" not in item_values:
            log.info(f"revenue or cost_of_goods_sold not in item_values, skip gross profit")
            return
        revenue = item_values["revenue"]
        cost_of_goods_sold = item_values["cost_of_goods_sold"]
        ret = revenue - cost_of_goods_sold
        return ret

    def _calc_ebitda(self, item_values: Dict):
        ret = 0.0
        ebit, depreciation_and_amortization = 0.0, 0.0
        if "ebit" in item_values and item_values["ebit"] is not None:
            ebit = item_values["ebit"]
        if "depreciation_and_amortization" in item_values and item_values["depreciation_and_amortization"] is not None:
            depreciation_and_amortization = item_values["depreciation_and_amortization"]  
        ret = ebit + depreciation_and_amortization
        log.info(f"calculate ebitda, ebit: {ebit}, depreciation_and_amortization: {depreciation_and_amortization}, ret: {ret}")
        return ret

    def _calc_ebit(self, item_values: Dict):
        ret = 0.0
        net_income, income_tax, interest_expense = 0.0, 0.0, 0.0
        if "net_income" in item_values and item_values["net_income"] is not None:
            net_income = item_values["net_income"]
        if "income_tax" in item_values and item_values["income_tax"] is not None:
            income_tax = item_values["income_tax"]
        if "interest_expense" in item_values and item_values["interest_expense"] is not None:
            interest_expense = item_values["interest_expense"]
        ret = net_income + income_tax + interest_expense
        log.info(f"calculate ebit, net_income: {net_income}, income_tax: {income_tax}, interest_expense: {interest_expense}, ret: {ret}")
        return ret

    def _calc_operating_expense(self, item_values: Dict):
        if "operating_expense" in item_values and item_values["operating_expense"] is not None:
            return item_values["operating_expense"]
        ret = 0.0
        research_and_development = 0.0
        general_and_admin_expense, selling_and_marketing_expense = 0.0, 0.0
        if "research_and_development" in item_values and item_values["research_and_development"] is not None:
            research_and_development = item_values["research_and_development"]
        if "general_and_admin_expense" in item_values and item_values["general_and_admin_expense"] is not None:
            general_and_admin_expense = item_values["general_and_admin_expense"]
        if "selling_and_marketing_expense" in item_values and item_values["selling_and_marketing_expense"] is not None:
            selling_and_marketing_expense = item_values["selling_and_marketing_expense"]
        ret = research_and_development + general_and_admin_expense+ selling_and_marketing_expense
        return ret
    
    def _calc_operating_margin(self, item_values: Dict):
        ret = None
        revenue, cost_of_goods_sold, research_and_development_expense = 0.0, 0.0, 0.0
        
        selling_and_admin_expense, general_and_admin_expense, selling_and_marketing_expense = 0.0, 0.0, 0.0
        if "selling_general_and_administrative_expenses" in item_values and item_values["selling_general_and_administrative_expenses"] is not None:
            selling_and_admin_expense = item_values["selling_general_and_administrative_expenses"]  
        else:
            if "general_and_admin_expense" in item_values and item_values["general_and_admin_expense"] is not None:
                general_and_admin_expense = item_values["general_and_admin_expense"]
            if "selling_and_marketing_expense" in item_values and item_values["selling_and_marketing_expense"] is not None:
                selling_and_marketing_expense = item_values["selling_and_marketing_expense"]
                selling_and_admin_expense = general_and_admin_expense + selling_and_marketing_expense
        
        if "revenue" in item_values and item_values["revenue"] is not None:
            revenue = item_values["revenue"]
        if "cost_of_goods_sold" in item_values and item_values["cost_of_goods_sold"] is not None:
            cost_of_goods_sold = item_values["cost_of_goods_sold"]
        if "research_and_development" in item_values and item_values["research_and_development"] is not None:
            research_and_development_expense = item_values["research_and_development"]
        ret = (revenue - cost_of_goods_sold - selling_and_admin_expense - research_and_development_expense) / revenue \
                if revenue != 0 else None
        log.info(f"calculate operating_margin, revenue: {revenue}, cost_of_goods_sold: {cost_of_goods_sold}, \
                 selling_and_admin_expense: {selling_and_admin_expense}, \
                 general_and_admin_expense: {general_and_admin_expense}, \
                 selling_and_marketing_expense: {selling_and_marketing_expense}, \
                 research_and_development_expense: {research_and_development_expense}, \
                 ret: {ret}")
        return ret
 

    def _calc_gross_margin(self, item_values: Dict):
        ret = None
        if "revenue" not in item_values or "gross_profit" not in item_values:
            log.info(f"revenue or gross_profit not in item_values, skip {item_values}")
            return
        revenue = item_values["revenue"]
        gross_profit = item_values["gross_profit"]
        if revenue is None or gross_profit is None:
            return None
        return gross_profit / revenue

    def extract_item_from_eq_statement(self, ticker: str, statement:Statement, statement_type: str, line_concepts_cfgs: Dict,
                                    tmp_result:Dict[str, float]):
        df = statement.to_dataframe(view="detailed")
        cols = ['concept', 'standard_concept',  
                'abstract',  'weight'] #, 'dimension', 'dimension_label']

        log.info(f"column is {df.columns}")
        log.info(f"concepts is {df['concept'].unique()}")
        log.info(f"standard concepts is {df['standard_concept'].unique()}")
        value_cols = [col for col in df.columns if 2 == col.count("-")]
        target_cols = cols + [value_cols[0]]
        log.info(f"total {statement_type} df for {ticker} is \n {df[target_cols]}")
        #tmp_result = {}
        for concept, concept_cfg in line_concepts_cfgs.items():
            tmp_result[concept] = None
            item_df = None
            log.info(f"concept is {concept}, cfg is {concept_cfg}")
            if concept_cfg["is_computed"]:
                continue
            if "custom_concepts" in concept_cfg and ticker in concept_cfg["custom_concepts"]:
                log.info(f"item_cfg is {concept_cfg}, ticker is {ticker}, concept is {concept_cfg['custom_concepts'][ticker]} ")
                item_df = df[ (df["concept"] == concept_cfg["custom_concepts"][ticker])][target_cols]
            elif "concepts" in concept_cfg:
                item_df = df[
                        (df["concept"].isin(concept_cfg["concepts"])) 
                         ][target_cols]
            elif "std_concepts" in concept_cfg:
                item_df = df[
                        (df["standard_concept"].isin(concept_cfg["std_concepts"])) 
                         ][target_cols]

            if item_df is not None and not item_df.empty :
                series = item_df[value_cols[0]]
                log.info(f"{concept}: {series}, len is {len(series)}, type is {type(series)}")
                if len(series) > 0:
                    tmp_result[concept] = series.values[0] 
                else:
                    log.warning(f"no valid value found for {concept}, {concept_cfg}")
            else:
                log.warning(f"no concept found for {concept}, {concept_cfg}")
                if "missing_default_value" in concept_cfg and tmp_result[concept] is None:
                    tmp_result[concept] = concept_cfg["missing_default_value"]
            
        return


    #def extract_income_statement(self, filing: Filing, line_items_cfgs: Dict):
    def extract_item_from_statement(self, ticker: str, statement:Statement, statement_type: str, line_concepts_cfgs: Dict,
                                    tmp_result:Dict[str, float]):
        df = statement.to_dataframe(
                            include_standardization=True, include_unit=True, 
                            include_point_in_time=True, matrix=True, view="detailed")
        cols = ['concept', 'standard_concept', "unit", 
                'abstract',  'weight'] #, 'dimension', 'dimension_label']

        log.info(f"column is {df.columns}")
        log.info(f"concepts is {df['concept'].unique()}")
        log.info(f"standard concepts is {df['standard_concept'].unique()}")
        value_cols = [col for col in df.columns if 2 == col.count("-")]

        target_cols = cols + [value_cols[0]]
        log.info(f"total {statement_type} df for {ticker} is \n {df[target_cols]}")
        #tmp_result = {}
        for concept, concept_cfg in line_concepts_cfgs.items():
            tmp_result[concept] = None
            item_df = None
            log.info(f"concept is {concept}, cfg is {concept_cfg}")
            if concept_cfg["is_computed"]:
                continue
            if "custom_concepts" in concept_cfg and ticker in concept_cfg["custom_concepts"]:
                log.info(f"item_cfg is {concept_cfg}, ticker is {ticker}, concept is {concept_cfg['custom_concepts'][ticker]} ")
                item_df = df[ (df["concept"] == concept_cfg["custom_concepts"][ticker])][target_cols]
            elif "concepts" in concept_cfg:
                item_df = df[
                        (df["concept"].isin(concept_cfg["concepts"])) 
                         ][target_cols]
            elif "std_concepts" in concept_cfg:
                item_df = df[
                        (df["standard_concept"].isin(concept_cfg["std_concepts"])) 
                         ][target_cols]

            if item_df is not None and not item_df.empty :
                if "dimension_label" in concept_cfg:
                    log.info(f"dimension_label is {concept_cfg['dimension_label']}")
                    log.info(f"item_df is {item_df["dimension_label"]}")
                    item_df = item_df[
                        (item_df["dimension_label"] is not None )&
                        (item_df["dimension_label"].str.contains(concept_cfg["dimension_label"]))
                        ]
            
            if item_df is not None and not item_df.empty :
                series = item_df[value_cols[0]]
                log.info(f"{concept}: {series}, len is {len(series)}, type is {type(series)}")
                if len(series) > 0:
                    tmp_result[concept] = series.values[0] 
                    if "negating" in concept_cfg and concept_cfg["negating"] == True:
                        tmp_result[concept] *= -1
                else:
                    log.warning(f"no valid value found for {concept}, {concept_cfg}")
            else:
                log.warning(f"no concept found for {concept}, {concept_cfg}")
                if "missing_default_value" in concept_cfg and tmp_result[concept] is None:
                    tmp_result[concept] = concept_cfg["missing_default_value"]
            
        return


class TestEdgarToolsFacade:
    def __init__(self):
        self.edgar_tools = EdgarToolsFacade()

    #CASH_FLOW_LINE_ITEMS
    def display_result(self, total_result: Dict):
        for result_key, items in total_result.items():
            ticker, period, start_date, end_date, limit = result_key.split("_")
            log.info(f"ticker is {ticker}, period is {period}, start_date is {start_date}, end_date is {end_date}, limit is {limit}")
            for idx, item in enumerate(items):
                log.info(f"{ticker} {idx}th {item}")

    @staticmethod
    def gen_key(ticker: str, period: str, start_date: str, end_date: str, limit: int):
        return f"{ticker}_{period}_{start_date}_{end_date}_{limit}"
    
    @staticmethod
    def split_key(result_key: str):
        return result_key.split("_")

    def get_all_expected_line_items(self, all_corps_info: List, target_items: List):
        total_result = {}
        for test_idx, corp_info in enumerate(all_corps_info):
            log.info(f"********Expected:try to query {test_idx + 1}th coprs: {corp_info["ticker"]}**********")
            ticker = corp_info["ticker"]
            start_date = corp_info["start_date"]
            end_date = corp_info["end_date"]
            period = corp_info["period"]
            limit = corp_info["limit"]
            result_key = TestEdgarToolsFacade.gen_key(ticker, period, start_date, end_date, limit)
            result = search_line_items(ticker, target_items,  end_date, period,limit)
            #result = query_all_financial_concepts(
            #    ticker, target_items, start_date, end_date, period,limit)
            log.info(f"result is {result}, type is {type(result)}")
            total_result[result_key] = result
        self.display_result(total_result)
        return total_result

    def get_all_actual_line_concepts(self, corp_infos: List, target_items: List):
        total_result = {}
        for corp_info in corp_infos:
            ticker = corp_info["ticker"]
            start_date = corp_info["start_date"]
            end_date = corp_info["end_date"]
            period = corp_info["period"]
            limit = corp_info["limit"]
            result_key = TestEdgarToolsFacade.gen_key(ticker, period, start_date, end_date, limit)  
            rets = self.edgar_tools.query_concepts(
                ticker, target_items, 
                datetime.strptime(end_date, "%Y-%m-%d"), 
                period, limit)
            total_result[result_key] = rets
        return total_result

class ConceptComparator:
    def __init__(self):
        pass

    def compare_concepts_4_all_corps(self, target_items: List, expected_rets_corps: Dict, actual_rets_corps: Dict):
        log.info(f"There are {len(expected_rets_corps)} expected rets and {len(actual_rets_corps)} actual rets")
        log.info(f"target_items is {target_items}")
        for result_key, expected_rets in expected_rets_corps.items(): 
            ticker, period, start_date, end_date, limit = TestEdgarToolsFacade.split_key(result_key)
            self.compare_concepts_4_one_corp(ticker, target_items, period, start_date, end_date, limit, 
                                             expected_rets, actual_rets_corps.get(result_key))

    def compare_concepts_4_one_corp(self, ticker, target_items: List, period, start_date, end_date, limit, expect_rets: List, actual_rets: List):
        for idx, expect_ret in enumerate(expect_rets):
            log.info(f"now compare {idx} for ticker {ticker}, start_date:{start_date}, end_date:{end_date}, period:{period}, limit:{limit}")
            actual_dict = actual_rets[idx]
            expect_dict = expect_ret.model_dump()
            total, passed = 0, 0    
            headers = ["Ticker", "Concept", "Expected", "Actual", "Match", "Deviation"]
            rows = []

            for concept in target_items:
                row = [ticker, concept]
                total += 1
                expect_value = expect_dict.get(concept)
                actual_value = actual_dict.get(concept)
                row.append(expect_value)
                row.append(actual_value)
                
                if isinstance(expect_value, str) and  expect_value == actual_value:
                    #log.info(f"concept {concept} str value is equal, E: {expect_value} = A: {actual_value}")
                    passed += 1
                    row.extend(["Yes", "0"])
                    rows.append(row)
                    continue
                if isinstance(expect_value, float) and isinstance(actual_value, float) and expect_value == 0:
                    if actual_value == 0:
                        passed += 1
                        row.extend(["Yes", "0"])
                        rows.append(row)
                    continue
                if isinstance(expect_value, float) and isinstance(actual_value, float) and expect_value != 0:
                    deviation = abs(expect_value - actual_value)/abs(expect_value)
                    if deviation < 0.15:
                        passed += 1
                        row.extend(["Yes", f"{deviation:.2f}"])
                    else:
                        row.extend(["No", f"{deviation:.2f}"])
                    rows.append(row)
                    continue

                log.warning(f"concept {concept} float value is not equal, E: {expect_value}  A: {actual_value}")
                row.extend(["No", ""])
                rows.append(row)

            sorted_data_asc = sorted(rows, key=lambda x: x[4], reverse=True)

            table = tabulate(sorted_data_asc, headers, tablefmt="github")
            log.info(f"Ticker {ticker} result: \n" + table)
            log.info(f"Ticker {ticker} {passed}/{total}={passed/total:.2%} concepts passed")   
            log.info(f"*"*64)



if __name__ == "__main__":
    test_facade = TestEdgarToolsFacade()
    target_items = ALL_CONCEPTS_ITEMS
    corp_infos = [
        {"ticker": "AAPL", "start_date": "2023-01-01", "end_date": "2026-12-31", "period": "annual", "limit": 1},
        {"ticker": "GOOGL", "start_date": "2025-01-01", "end_date": "2026-03-31", "period": "annual", "limit": 1},
        {"ticker": "MSFT",  "start_date": "2025-01-01", "end_date": "2026-03-31", "period": "annual", "limit": 1},
        {"ticker": "NVDA",  "start_date": "2026-01-01", "end_date": "2026-03-31", "period": "annual", "limit": 1},
        {"ticker": "TSLA",  "start_date": "2026-01-01", "end_date": "2026-03-31", "period": "annual", "limit": 1},
    ]
    
    actual_rets = test_facade.get_all_actual_line_concepts(corp_infos, target_items)
    expected_rets = test_facade.get_all_expected_line_items(corp_infos, target_items)

    comparator = ConceptComparator()
    comparator.compare_concepts_4_all_corps(target_items, expected_rets, actual_rets)
