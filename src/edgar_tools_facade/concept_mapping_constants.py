ALL_DEPENDENCY_CONCEPTS = {
    "income_statement": [ 
        "cost_of_goods_sold", 
        "selling_general_and_administrative_expenses", "selling_and_marketing_expense", "general_and_admin_expense" , 
        "non_operating_income_expense",
        "income_tax", "pretax_income", "effective_tax_rate", 
    ],
    
    "balance_sheet": [ 
        "intangible_assets" , "goodwill" , "commercial_paper", "short_term_debt", 
        "long_term_debt_current", "long_term_debt_noncurrent", "operating_lease_noncurrent",
        "stock_close_price"
    ], 
        
    "cash_flow_statement": [ 
        "operating_cash_flow", "proceeds_from_issuance_of_common_stock", 
        "payment_for_repurchase_of_common_stock", "payment_related_to_tax_withholding_for_share_based_compensation",
    ],
    "equity": [
        "shares_issued", "shares_issued_during_period", "shares_repurchased_equity_during_period",
    ]
}

all_line_items = {
    # 利润表 Income Statement
    "income_statement": [
        "revenue",                          #Pass                             
        "net_income",                       #Pass
        "operating_income",                 #Pass
        "research_and_development",         #Pass
        "earnings_per_share",               #Pass
        "gross_margin",                     #Pass
        "gross_profit",                     #Pass
        "operating_expense",                #Pass
        
        "ebit",                             
        "operating_margin",                 #Passed 3corps
        "ebitda",
        "interest_expense",                 #Pass
    ],
    
    # 资产负债表 Balance Sheet
    "balance_sheet": [
        "goodwill_and_intangible_assets",   #Pass
        "cash_and_equivalents",             #Pass
        "shareholders_equity",              #Pass
        "total_assets",                     #Pass
        "current_assets",                   #pass
        "total_liabilities",                #Pass
        "current_liabilities",              #Pass
        "working_capital",                  #pass
        "total_debt",                       #Pass
        "debt_to_equity",                   #Pass
        "outstanding_shares",
        
        "book_value_per_share" ,            #需要借助其他statement计算得到, in chinese, it means 股票账面价值
        "return_on_invested_capital"        #Need operating income
    ],

    # 现金流量表 Cash Flow Statement
    "cash_flow_statement": [
        "capital_expenditure",                      #Pass
        "free_cash_flow",                           #Pass 
        "dividends_and_other_cash_distributions",   #Pass
        "depreciation_and_amortization",            #Pass
        "issuance_or_purchase_of_equity_shares",    #Partial Pass Failed at ticker='AAPL', report_period='2025-09-27'
        "cash_and_equivalents",                     #Pass 
    ],
}

INCOME_LINE_ITEMS = all_line_items["income_statement"]
BALANCE_SHEET_LINE_ITEMS = all_line_items["balance_sheet"]
CASH_FLOW_LINE_ITEMS = all_line_items["cash_flow_statement"]
ALL_CONCEPTS_ITEMS = INCOME_LINE_ITEMS + BALANCE_SHEET_LINE_ITEMS + CASH_FLOW_LINE_ITEMS

EDGAR_TOOLS_LINE_ITEMS_MAP = {
    "revenue": {
        "stmt": "IS",
        "std_concepts": ["Revenue","Revenues", 
                         "RevenueFromContractWithCustomer", "SalesRevenueNet", "TotalRevenue", "Net sales"],
        "is_computed": False
    },
   
    "research_and_development": {
        "stmt": "IS",
        "std_concepts": ["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenses"],
        "is_computed": False
    },

    "net_income": {
        "stmt": "IS",
        "std_concepts": ["NetIncomeLoss", "NetIncome", "NetEarnings" ],
        "is_computed": False
    },
    
    "operating_income": {
        "stmt": "IS",
        "std_concepts": ["OperatingIncomeLoss", "OperatingProfit", "Operating income", "Income from operations"],
        "is_computed": False
    },

    "cost_of_goods_sold": {
        "stmt": "IS",
        "std_concepts": ["CostOfGoodsAndServicesSold"],
        "is_computed": False,
    },

    "gross_profit": {
        "stmt": "IS",
        "is_computed": True,
        "formula": "revenue - cost_of_goods_sold"
    },
 

    "gross_margin": {
        "stmt": "IS",
        "is_computed": True,
        "formula": "(revenue - cost_of_goods_sold) / revenue"
    },

    "selling_and_marketing_expense": {
        "stmt": "IS",
        "concepts": ["us-gaap_SellingAndMarketingExpense"],
        "is_computed": False,
    },
 
    "general_and_admin_expense": {
        "stmt": "IS",
        "concepts": ["us-gaap_GeneralAndAdministrativeExpense"],
        "is_computed": False,
    },

    "sell_and_admin_expense":{
        "stmt": "IS",
        "concepts": ["us-gaap_SellingGeneralAndAdministrativeExpense"],
        "is_computed": False,
    },
 
    "operating_expense": {
        "stmt": "IS",
        "is_computed": False,
        "std_concepts": ["TotalOperatingExpenses"],
    }, 

    "operating_margin": {
        "stmt": "IS",
        "is_computed": True,
        "formula": "(revenue - cost_of_goods_sold - selling_and_admin_expense - research_and_development) / revenue",
        "url": "https://www.investopedia.com/terms/o/operatingmargin.asp",
        "cn": "运营利润率",
    },

    "non_operating_income_expense": {
        "stmt": "IS",
        "std_concepts": ["NonoperatingIncomeExpense"],
        "is_computed": False,
    },
    "interest_expense": {
        "stmt": "IS",
        "is_computed": False,
        "std_concepts": ["InterestExpense"],
    },
  
    "pretax_income": {
        "stmt": "IS",
        "std_concepts": ["PretaxIncomeLoss"],
        "is_computed": False,
        "cn": "息税前收入",
    },

    "income_tax":{
        "stmt": "IS",
        "std_concepts": ["IncomeTaxes"],
        "is_computed": False,
        "cn": "所得税",
    },

    "effective_tax_rate": {
        "stmt": "IS",   
        "std_concepts": ["EffectiveTaxRate"],
        "is_computed": False
    },

    "ebit": {
        "stmt": "IS",
        "is_computed": True,
        "cn": "息税前利润",
        "en": "Earnings Before Interest and Taxes",
        "formula": "net_income + income_tax + interest_expense",
        "url": "https://www.investopedia.com/terms/e/ebit.asp"
    },


    "ebitda": {
        "stmt": "IS",
        "is_computed": True,
        "formula": "ebit + depreciation_and_amortization"
    },

    "shareholders_equity": {
        "stmt": "BS",
        "std_concepts": ["AllEquityBalance"],
        "is_computed": False
    },
 
    "total_assets": {
        "stmt": "BS",
        "std_concepts": ["Assets"],
        "is_computed": False
    },

    "total_liabilities": {
        "stmt": "BS",
        "std_concepts": ["Liabilities"],
        "is_computed": False
    },
    "debt_to_equity": {
        "stmt": "BS",
        "is_computed": True,
        "formula": "total_liabilities / shareholders_equity"
    },

    "working_capital": {
        "stmt": "BS",
        "is_computed": True,
        "formula": "current_assets - current_liabilities"
    },
    
    "book_value_per_share": {
        "stmt": "BS",
        "is_computed": True,
        "formula": "shareholders_equity / outstanding_shares"
    },

    "outstanding_shares": {
        "stmt": "BS",
        "concepts": ["us-gaap_CommonStockSharesOutstanding"],
        "is_computed": False,
    },


    "cash_and_equivalents": {
        "stmt": "BS",
        "std_concepts": ["CashAndMarketableSecurities", "CashAndCashEquivalents"],
        "is_computed": False
    },
    
    "capital_expenditure": {
        "stmt": "CF",
        "std_concepts": ["CapitalExpenses"],
        "is_computed": False,
    },

    
    "operating_lease_liability_noncurrent": {
        "stmt": "BS",
        "std_concepts": ["Long-term debt"],
        "std_concepts": ["OperatingLeaseLiabilityNoncurrent"],
        "is_computed": False,
    },

    "short_term_debt": {
        "stmt": "BS",
        "std_concepts": ["ShortTermDebt"],
        "is_computed": False,
    },

    "commercial_paper": {
        "stmt": "BS",
        "concepts": ["us-gaap_CommercialPaper"],
        "is_computed": False,
        "cn": "商业票据",
        "missing_default_value": 0.0,
    },

    "long_term_debt_current": {
        "stmt": "BS",
        "concepts": ["us-gaap_LongTermDebtCurrent"],
        "custom_concepts": {
            "TSLA": "tsla_LongTermDebtAndFinanceLeasesCurrent",
        },
        "is_computed": False,
    },

    "long_term_debt_noncurrent": {
        "stmt": "BS",
        "concepts": ["us-gaap_LongTermDebtNoncurrent"],
        "custom_concepts": {
            "TSLA": "tsla_LongTermDebtAndFinanceLeasesNoncurrent",
        },
        "is_computed": False,
    },

    "operating_lease_noncurrent": {
        "stmt": "BS",
        "std_concepts": ["OperatingLeaseNonCurrentDebtEquivalent", 
                         "OperatingLeaseLiabilityNoncurrent"],
        "is_computed": False ,
    },

    "total_debt": {
        "stmt": "BS",
        "is_computed": True,
        "formula": "long_term_debt_current + long_term_debt_noncurrent + operating_lease_noncurrent",
        "cn": "总债务",
    },
   
    "goodwill": {
        "stmt": "BS",
        "std_concepts": ["Goodwill"],
        "is_computed": False,
    },
    "intangible_assets": {
        "stmt": "BS",
        "std_concepts": ["IntangibleAssets"], 
        "is_computed": False,
    },

    "goodwill_and_intangible_assets": {
        "stmt": "BS",
        "is_computed": True,
        "formula": "goodwill + intangible_assets",
        "cn": "资产价值与无形资产",
    },

   "income_tax_expense": {
        "stmt": "IS",
        "std_concepts": ["Provision for income taxes", "Income tax expense", "Income tax expense, net"],
        "is_computed": False,
    },
    
    "operating_cash_flow": {
        "stmt": "CF",
        "concepts": ["us-gaap_NetCashProvidedByUsedInOperatingActivities"],
        "is_computed": False,
    },
    "net_cash_flow_from_operations": {
       
        "std_concepts": [],
        "std_concepts": ["NetCashProvidedByUsedInOperatingActivities"],
        "is_computed": False,
    },
    "net_cash_flow_from_investing": {
        "stmt": "CF",
        "std_concepts": [],
        "std_concepts": ["NetCashProvidedByUsedInInvestingActivities"],
        "is_computed": False,
    },
    "net_cash_flow_from_financing": {
        "stmt": "CF",
        "std_concepts": [],
        "std_concepts": ["NetCashProvidedByUsedInFinancingActivities"],
        "is_computed": False,
        "cn": "融资现金流量",
    },

    "free_cash_flow": {
        "stmt": "CF",
        "std_concepts": ["FreeCashFlow"],
        "is_computed": True,
        "formula": "operating_cash_flow - capital_expenditure",
        "cn": "自由现金流量",
    },
  
     "cost_of_revenue": {
        "stmt": "IS",
        "std_concepts": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
        "is_computed": False,
    },

    "earnings_per_share": {
        "stmt": "IS",
        "concepts": ["us-gaap_EarningsPerShareBasic"],
        "std_concepts": ["EarningsPerShare", "EarningsPerShareBasic"],
        "is_computed": False,
    },
    "earnings_per_share_diluted": {
        "stmt": "IS",
        "std_concepts": ["EarningsPerShareDiluted"],
        "is_computed": False,
    },

    "general_and_administrative_expenses": {
        "stmt": "IS",
        "std_concepts": ["GeneralAndAdministrativeExpense" ],
        "is_computed": False,
    },

    "sales_and_marketing_expenses": {
        "stmt": "IS",
        "std_concepts": [
            "SellingGeneralAndAdministrativeExpense",
            "SellingAndMarketingExpense"],
            
        "is_computed": False,
    },

    "selling_general_and_administrative_expenses": {
        "stmt": "IS",
        "std_concepts": ["SellingGeneralAndAdministrativeExpenses",
                         "SellingGeneralAndAdministrativeExpense", 
                         "GeneralAndAdministrativeExpense",
                         "SellingGeneralAndAdminExpenses",
                         ],
        "is_computed": False,
    },
    "current_assets": {
        "stmt": "BS",
        "std_concepts": ["CurrentAssetsTotal"],
        "is_computed": False,
    },
    "current_liabilities": {
        "stmt": "BS",
        "std_concepts": ["CurrentLiabilitiesTotal"],
        "is_computed": False,
    },



    "accumulated_other_comprehensive_income": {
        "stmt": "BS",
        "std_concepts": ["·",
                         "AccumulatedOtherComprehensiveIncomeLossNetOfTax"
                         ],
        "is_computed": False,
    },


    "inventory": {
        "stmt": "BS",
        "std_concepts": ["InventoryNet"],
        "is_computed": False,
        "missing_default_value": 0.0
    },
    "property_plant_and_equipment": {
        "stmt": "BS",
        "std_concepts": ["PropertyPlantAndEquipmentNet"],
        "is_computed": False,
    },
    "retained_earnings": {
        "stmt": "BS",
        "std_concepts": ["RetainedEarningsAccumulatedDeficit"],
        "is_computed": False,
    },

    "dividends_and_other_cash_distributions": {
        "stmt": "CF",
        "concepts": ["us-gaap_PaymentsOfDividendsCommonStock", "us-gaap_PaymentsOfDividends"],
        "is_computed": False,
        "missing_default_value": 0.0,
        "cn": "股息和其他现金分布",
    },
 
    "effect_of_exchange_rate_changes": {
        "stmt": "CF",
        "std_concepts": ["EffectOfExchangeRateChangesOnCashAndCashEquivalents",
                         "EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                         "EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations",
                         ],
        "missing_default_value": 0.0,
        "is_computed": False,
    },

    ########################  Failed #############################################
    "repayment_of_debt_securities": {
        "stmt": "CF",
        "std_concepts": ["RepaymentsOfDebt", 
                         "RepaymentsOfDebtAndCapitalLeaseObligations",
                         "RepaymentsOfDebtMaturingInMoreThanThreeMonths",
                         "RepaymentsOfLongTermDebt",
                         "RepaymentsOfConvertibleDebt"
                         ],
        "is_computed": False,
        "missing_default_value": 0.0,
        "negating": True,
    },

    "issuance_of_debt_securities": {
        "stmt": "CF",
        "std_concepts": ["ProceedsFromSaleOfAvailableForSaleSecuritiesDebt"],
       "is_computed": False,
        "negating": True,
    },
     
    "proceeds_from_issuance_of_common_stock": {
        "stmt": "CF",
        "concepts": ["us-gaap_ProceedsFromStockPlans",
                     "us-gaap_ProceedsFromIssuanceOfCommonStock",
                     "us-gaap_ProceedsFromIssuanceOfSharesUnderIncentiveAndShareBasedCompensationPlansIncludingStockOptions" #TLSA
                     ], 
        "is_computed": False,
        "missing_default_value": 0.0,
        "custom_concepts": {
            "GOOGL": "goog_NetProceedsPaymentsRelatedToStockBasedAwardActivities",
        },
    },
    
    "payment_for_repurchase_of_common_stock": {
        "stmt": "CF",
        "concepts": ["us-gaap_PaymentsForRepurchaseOfCommonStock"],
        "is_computed": False,
        "missing_default_value": 0.0,
    },

    "payment_related_to_tax_withholding_for_share_based_compensation": {
        "stmt": "CF",
        "concepts": ["us-gaap_PaymentsRelatedToTaxWithholdingForShareBasedCompensation"],
        "is_computed": False,
        "missing_default_value": 0.0,
    },

    "issuance_or_purchase_of_equity_shares": {
        "stmt": "CF",
        "std_concepts": [],
        "is_computed": True,
        "formula": "proceeds_from_issuance_of_common_stock - payment_for_repurchase_of_common_stock - payment_related_to_tax_withholding_for_share_based_compensation",
        "cn": "发行或购买股票",  
    },
    
    "issuance_of_debt": {
        "stmt": "CF",
        "std_concepts": ["ProceedsFromIssuanceOfLongTermDebt", 
                         "ProceedsFromIssuanceOfDebt"],
        "is_computed": False,
        "missing_default_value": 0.0,
    },
   
    "business_acquisitions_and_disposals": {
        "stmt": "CF",
        "std_concepts": ["PaymentsToAcquireBusinessesNetOfCashAcquired",
                         "AcquisitionsNetOfCashAcquiredAndPurchasesOfIntangibleAndOtherAssets",
                         ],
        "is_computed": False,
        "missing_default_value": 0.0,
        "negating": True,
    },
    "change_in_cash_and_equivalents": {
        "stmt": "CF",
        "std_concepts": ["IncreaseDecreaseInCashAndCashEquivalents",
                         "CashAndCashEquivalentsPeriodIncreaseDecrease",
                         "IncreaseDecreaseInAccountsPayable",
                         "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect"
                         ],
        "is_computed": False,
    }, 

    "depreciation_and_amortization": {
        "stmt": "CF",
        "std_concepts": ["DepreciationExpense"],
        "is_computed": False,
        "custom_concepts": {
            "MSFT":"msft_DepreciationAmortizationAndOther",
            "TSLA":"tsla_DepreciationAmortizationAndImpairment"},
        "cn": "折旧和摊销",
    },

    "proceeds_from_sale_of_short_term_investments": {
        "stmt": "CF",
        "std_concepts": ["ProceedsFromSaleOfShortTermInvestments",
                         "ProceedsFromInvestments",
                         "ProceedsFromRepaymentsOfCommercialPaper",
                         ],
        "is_computed": False,
        "missing_default_value": 0.0,
    },

    "proceeds_from_maturities_investments": {
        "stmt": "CF",
        "std_concepts": ["ProceedsFromMaturitiesPrepaymentsAndCallsOfAvailableForSaleSecurities",
                         "ProceedsFromSaleMaturityAndCollectionsOfInvestments" ],
        "is_computed": False,
        "missing_default_value": 0.0,
    },
    "proceeds_from_other_financing_activities": {
        "stmt": "CF",
        "std_concepts": ["ProceedsFromPaymentsForOtherFinancingActivities", 
                         "PaymentsForProceedsFromOtherInvestingActivities"],
        "is_computed": False,
        "missing_default_value": 0.0,
    },

    "payments_to_acquire_investments": {
        "stmt": "CF",
        "std_concepts": [""],
        "is_computed": False,
        "missing_default_value": 0.0,
        "negating": True,
    },

    "investment_acquisitions_and_disposals": {
        "stmt": "CF",
        "std_concepts": [],
        "is_computed": True,
    },

    "share_based_compensation": {
        "stmt": "CF",
        "is_computed": False,
        "std_concepts": ["ShareBasedCompensation"],
    },

    "deferred_revenue": {
        "stmt": "BS",
        "std_concepts": ["ContractWithCustomerLiabilityCurrent"],
        "is_computed": False,
    },

    "non_current_assets": {
        "stmt": "BS",
        "std_concepts": ["AssetsNoncurrent", "OtherAssetsNoncurrent"],
        "is_computed": False,
    },
    "non_current_liabilities": {
        "stmt": "BS",
        "std_concepts": ["LiabilitiesNoncurrent", "OtherLiabilitiesNoncurrent"],
        "is_computed": False,
    },

    "non_current_debt": {
        "stmt": "BS",
        "std_concepts": ["DebtNoncurrent"],
        "is_computed": False,
    },
    "non_current_investments": {
        "stmt": "BS",
        "std_concepts": ["InvestmentsNoncurrent"],
        "is_computed": False,
    },
    
   "current_debt": {
        "stmt": "BS",
        "std_concepts": [ "Short-term debt"],
        "is_computed": False,
    },
    "current_investments": {
        "stmt": "BS",
        "std_concepts": ["Short-term investments"],
        "is_computed": False,
    },
    
    "dividend_per_common_share": {
        "stmt": "EQ",
        "std_concepts": ["DividendPerCommonShare"],
        "is_computed": False,
    },


    "weighted_average_shares": {
        "stmt": "IS",
        "std_concepts": ["WeightedAverageNumberOfSharesOutstandingBasic"],
        "is_computed": False,
    },
    "weighted_average_shares_diluted": {
        "stmt": "IS",
        "std_concepts": [ "WeightedAverageNumberOfDilutedSharesOutstanding" ],
        "is_computed": False,
    },


    "stock_based_compensation_expense": {
        "stmt": "IS",
        "std_concepts": ["AllocatedShareBasedCompensationExpense",
                        "ShareBasedCompensationExpense" ,                       
                         ],
        "is_computed": False,
    },
    "restructuring_charges": {
        "stmt": "IS",
        "std_concepts": ["RestructuringCharges", "RestructuringChargesNet"],
        "is_computed": False,
    },


    "common_stock_shares_issued": {
        "stmt": "IS",
        "std_concepts": ["CommonStockSharesIssued"],
        "is_computed": False,
    },
    "treasury_stock_shares": {
        "stmt": "IS",
        "std_concepts": ["TreasuryStockShares"],
        "is_computed": False,
    },
 
    "return_on_invested_capital": {
        "stmt": "CF",
        "std_concepts": [],
        "is_computed": True,
        "formula": "ebit * (1 - effective_tax_rate) / (total_debt + shareholders_equity)",
        "url": "https://www.investopedia.com/terms/r/returnoninvestedcapital.asp",
        "cn": "投资资本回报率",
    },
   }