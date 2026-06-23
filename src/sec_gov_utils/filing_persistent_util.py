import os
import sys
sys.path.append(".")
from ai_lab_comm.log_util import log
from edgar_tools_facade import EdgarToolsFacade
from edgar import Filing    
from edgar.xbrl import XBRL

class FilingPersistentUtil:
    def __init__(self, local_storage_dir):
        self.local_storage_dir = local_storage_dir

    def exists(self, cik:int, ticker:str, accession_number:str) -> bool:
        filing_path = os.path.join(self.local_storage_dir, f"{cik}_{ticker}/{accession_number}.pkl")
        return os.path.exists(filing_path)
    
    def save(self, cik:int, ticker:str, filing: Filing):
        access_number = filing.accession_number

        filing_path = os.path.join(self.local_storage_dir, f"{cik}_{ticker}/")
        if not os.path.exists(filing_path):
            os.makedirs(filing_path)
        if os.path.exists(f"{filing_path}/{access_number}.pkl"):
            log.info(f"{cik}, {ticker}, {access_number}.pkl already exists.")
            return
        filing.save(filing_path)
    



    def load(self, cik:int, ticker:str, accession_number:str) -> Filing:
        filing_path = os.path.join(self.local_storage_dir, f"{cik}_{ticker}/{accession_number}.pkl")
        filing = Filing.load(filing_path)
        return filing


if __name__ == '__main__':
    
    facade = EdgarToolsFacade()
    target_ticker, target_period = "NVDA", "quarterly"
    target_ticker, target_period = "NVDA", "annual"# "annual"
    target_year, target_quarter = 2025, None
    tenK = facade.load_corp_dataset(target_ticker, target_period, 
                                      target_year, target_quarter)
    

    local_storage_dir = "/ssd/datasets/edgar/filing/"
    persistent_util = FilingPersistentUtil(local_storage_dir)
    persistent_util.save(tenK.cik, target_ticker, tenK)

    loaded_tenK = persistent_util.load(tenK.cik, target_ticker, tenK.accession_number)
    log.info(loaded_tenK)
    xbrl = XBRL.from_filing(loaded_tenK)
    cashflow_stat = xbrl.statements.cashflow_statement()
    income_stat = xbrl.statements.income_statement()
    balance_sheet_stat = xbrl.statements.balance_sheet()
    log.info(income_stat)
    log.info(balance_sheet_stat)
    log.info(cashflow_stat)
