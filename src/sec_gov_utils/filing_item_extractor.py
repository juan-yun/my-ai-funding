from typing import List, Dict, Any, Optional
import sys
sys.path.append("./")
from ai_lab_comm.log_util import log

from edgar import Filing
from edgar.xbrl import *
from edgar_tools_facade import EdgarToolsFacade

class FilingItemExtractor:
    def __init__(self):
        pass
    
    def load_filing(self, filing:Filing):
        return filing
    
    def extract_items(self, items:list, filing:Filing):
        return filing.items
    

if __name__ == '__main__':
    facade = EdgarToolsFacade()
    target_ticker, target_period = "NVDA", "quarterly"
    target_ticker, target_period = "NVDA", "annual"# "annual"
    target_ticker, target_period = "AAPL", "annual"# "annual"
    target_year, target_quarter = 2025, None

    tenK = facade.load_corp_dataset(target_ticker, target_period, 
                                      target_year, target_quarter)
    xbrl = XBRL.from_filing(tenK)

    facts = xbrl.facts

    income_facts = facts.get_statement_facts('IncomeStatement')
    log.info(f"income sheet has {len(income_facts)} facts")
    
    log.info(f"\n{income_facts.dtypes}")
    concern_cols = ['concept', 'value',  #'label', 
                    'numeric_value', 'period_start', 'period_end', 'unit_ref']
    log.info(income_facts[concern_cols])
    target_items = ['us-gaap:Revenues', 
                    'us-gaap:NetIncomeLoss', 
                    'us-gaap:OperatingIncomeLoss',
                    'us-gaap:ResearchAndDevelopmentExpense' ]
    # info = income_facts[income_facts['label'].isin(target_items)]
    info = income_facts[( income_facts['period_end'] > f"{target_year}-01-01") 
                        & (income_facts['concept'].isin(target_items))
                        & (income_facts['dim_us-gaap_StatementEquityComponentsAxis'].isna())
                        & (income_facts['dim_us-gaap_StatementBusinessSegmentsAxis'].isna())
                        & (income_facts['dim_srt_StatementGeographicalAxis'].isna())
                        & (income_facts['dim_srt_ProductOrServiceAxis'].isna())
                        #& (income_facts['dim_us-gaap_NatureOfExpenseAxis'].isna())
                        #& (income_facts['dim_srt_ConsolidationItemsAxis'].isna())
                        ][concern_cols]
    info = info.drop_duplicates()
    log.info(f"\n{info}")
    log.info(info.dtypes)
