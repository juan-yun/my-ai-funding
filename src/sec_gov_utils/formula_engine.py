"""
Formula Engine for handling financial statement formulas based on cal.tsv
cal.tsv contains calculation relationships between financial statement items
Columns: adsh, grp, arc, negative, ptag, pversion, ct, cversion
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import os
import logging

import sys
sys.path.append(".")
from ai_lab_comm.log_util import log

from fin_stat_dir_resolver import FinStatNotesDirResolver
from fin_stat_notes_ds_facade import FinStatementNotesDatasetFacade


class FormulaEngine:
    """
    Formula Engine responsible for generating financial statement formulas based on cal.tsv
    Uses adsh as key to filter formulas for specific financial statements
    """
    
    def __init__(self):
        pass
    
    def _process_formulas(self) -> Dict[str, pd.DataFrame]:
        """
        Process the cal.tsv data to group formulas by adsh for efficient lookup
        """
        # Group the cal data by adsh
        grouped = self.cal_df.groupby('adsh')
        return {adsh: group for adsh, group in grouped}
    
    def get_formulas_for_adsh(self, adsh: str) -> Optional[pd.DataFrame]:
        """
        获取指定adsh（财务报表）的所有公式
        
        Args:
            adsh: 识别特定财务报表的存取号字符串
            
        Returns:
            包含给定adsh计算关系的DataFrame，如果不存在则返回None
        """
        return self.formulas_by_adsh.get(adsh, None)
    
    def build_calculation_tree(self, adsh: str) -> Dict[str, Any]:
        """
        为特定adsh构建计算树，显示父子关系
        
        Args:
            adsh: 识别特定财务报表的存取号字符串
            
        Returns:
            表示计算树的字典
        """
        # Check if calculation tree is already cached
        if adsh in self._calculation_trees_cache:
            return self._calculation_trees_cache[adsh]
        
        formulas = self.get_formulas_for_adsh(adsh)
        if formulas is None:
            return {}
        
        # Create a tree structure where each parent tag maps to its children
        calc_tree = {}
        for _, row in formulas.iterrows():
            parent_tag = row['ptag']  # 父标签（计算出的项目）
            child_tag = row['ctag']  # 子标签（组成项目）
            arcrole = row['arc']  # 关系类型
            negative = row['negative']  # 是否否定值
            
            if parent_tag not in calc_tree:
                calc_tree[parent_tag] = []
            
            calc_tree[parent_tag].append({
                'child_tag': child_tag,
                'arcrole': arcrole,
                'negative': bool(negative),
                'weight': -1 if negative else 1
            })
        
        # Cache the calculation tree
        self._calculation_trees_cache[adsh] = calc_tree
        return calc_tree
    
    def generate_all_formulas_for_adsh(self, adsh: str) -> Dict[str, str]:
        """
        自动生成指定adsh中所有ptag的计算公式
        
        Args:
            adsh: 识别特定财务报表的存取号字符串
            
        Returns:
            字典，键为ptag，值为对应的公式字符串
        """
        calc_tree = self.build_calculation_tree(adsh)
        formulas = {}
        
        for parent_tag, children in calc_tree.items():
            formula_parts = []
            for comp in children:
                child_tag = comp['child_tag']
                weight = comp['weight']
                
                if weight == -1:
                    formula_parts.append(f"-{child_tag}")
                else:
                    formula_parts.append(child_tag)
            
            formula_str = f"{parent_tag} = " + " + ".join(formula_parts).replace("+ -", "- ")
            formulas[parent_tag] = formula_str
        
        return formulas
    
    def generate_formula(self, adsh: str, target_tag: str) -> Optional[str]:
        """
        Generate a formula string for a specific tag based on calculation relationships
        
        Args:
            adsh: Accession number string identifying a specific financial statement
            target_tag: The tag for which to generate a formula
            
        Returns:
            String representation of the formula or None if not found
        """
        calc_tree = self.build_calculation_tree(adsh)
        if target_tag not in calc_tree:
            return None
        
        components = calc_tree[target_tag]
        formula_parts = []
        
        for comp in components:
            child_tag = comp['child_tag']
            weight = comp['weight']
            
            if weight == -1:
                formula_parts.append(f"-{child_tag}")
            else:
                formula_parts.append(child_tag)
        
        return f"{target_tag} = " + " + ".join(formula_parts).replace("+ -", "- ")
    
    def apply_calculations(self, adsh: str, data_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Apply all calculation formulas for a given adsh to compute derived values
        
        Args:
            adsh: Accession number string identifying a specific financial statement
            data_dict: Dictionary containing known financial statement values
            
        Returns:
            Updated dictionary with calculated values
        """
        calc_tree = self.build_calculation_tree(adsh)
        updated_data = data_dict.copy()
        
        # Sort calculation tree to handle dependencies properly
        # We'll calculate iteratively until no more values can be computed
        changed = True
        max_iterations = 10  # Prevent infinite loops
        iterations = 0
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for parent_tag, children in calc_tree.items():
                # Check if all child values are available to calculate the parent
                all_children_available = all(
                    child['child_tag'] in updated_data for child in children
                )
                
                if all_children_available and parent_tag not in updated_data:
                    # Calculate the parent value
                    calculated_value = 0.0
                    for child in children:
                        child_value = updated_data[child['child_tag']]
                        weight = child['weight']
                        calculated_value += weight * child_value
                    
                    updated_data[parent_tag] = calculated_value
                    changed = True
        
        return updated_data
    
    def load_from_tsv_file(self, tsv_path: str, columns: List[str] = None):
        """
        Load FormulaEngine from a cal.tsv file
        
        Args:
            tsv_path: Path to the cal.tsv file
            columns: List of columns to load (defaults to standard cal.tsv columns)
        """
        if columns is None:
            columns = ["adsh", "grp", "arc", "negative", "ptag", "pversion", "ctag", "cversion"]
        
        log.info(f"Loading cal.tsv from {tsv_path}")
        self.cal_df = pd.read_csv(tsv_path, sep="\t", usecols=columns, low_memory=False)
        log.info(f"Loaded {len(self.cal_df)} rows from cal.tsv")
        
        # Rebuild the formulas by adsh
        self.formulas_by_adsh = self._process_formulas()
        # Clear the cache since data has changed
        self._calculation_trees_cache = {}



def create_formula_engine(local_ds_dir: str) -> FormulaEngine:
    """
    Convenience function to create a FormulaEngine from the financial statement directory
    
    Args:
        local_ds_dir: Directory containing financial statement datasets
        
    Returns:
        FormulaEngine instance
    """
    cal_tsv_path = os.path.join(local_ds_dir, "cal.tsv")
    if not os.path.exists(cal_tsv_path):
        raise FileNotFoundError(f"cal.tsv not found at {cal_tsv_path}")
    
    return FormulaEngine.from_tsv_file(cal_tsv_path)

def test_corp_calculation_formulas(ticker:str, period:str, fiscal_year:int, fiscal_quarter:int):

    log.info(f"begin to query for line items of {ticker}, {period}, {fiscal_year}Q{fiscal_quarter}")
    local_fs_notes_dir = "/ssd/datasets/edgar/financial_dataset_notes"
    dir_resolver = FinStatNotesDirResolver(local_fs_notes_dir)
    dir, adsh, period = dir_resolver.query_adsh(ticker, fiscal_year, fiscal_quarter)
    if dir is None or adsh is None:
        log.warning(f"no dir found for {ticker}, {fiscal_year}, {fiscal_quarter}")
        return None

    cal_file_path = os.path.join(dir, "cal.tsv")
    log.info(f"dir is {dir}, adsh is {adsh}, period is {period}, cal_file_path is {cal_file_path}")
    engine = FormulaEngine()
    engine.load_from_tsv_file(cal_file_path)
    all_formulas = engine.generate_all_formulas_for_adsh(adsh)
    log.info(f"total {len(all_formulas)} formulas for {ticker}, {period}, {fiscal_year}Q{fiscal_quarter}")
    for target_tag, formula in all_formulas.items():
        log.info(f"Ticker:{ticker}, ParentTag:{target_tag}: {formula}")
    #for line_item in target_tags:
    #    formula = engine.generate_formula(adsh, line_item)
    #    log.info(f"formula for {line_item} is {formula}")

target_tags = [
    "InventoryNet",
   ]


def test_all_corp_actual():
    test_inputs =[
        {"ticker": "NVDA", "fiscal_year":2026, "fiscal_quarter":4, "period": "annual"},
        #{"ticker": "GOOGL", "fiscal_year":2025, "fiscal_quarter":4, "period": "annual"},
        #{"ticker": "MSFT", "fiscal_year":2025, "fiscal_quarter":4, "period": "annual"},
        #{"ticker": "AAPL", "fiscal_year":2025, "fiscal_quarter":4, "period": "annual"},
        #{"ticker": "TSLA", "fiscal_year":2025, "fiscal_quarter":4, "period": "annual"},
    ]
    total_result = [] 
    for test_idx, test_input in enumerate(test_inputs):
        ret = test_corp_calculation_formulas(**test_input)

# Example usage:
if __name__ == "__main__":
    # Example of how to use the formula engine
    # This would typically be called with the path to your cal.tsv file
    # engine = FormulaEngine.from_tsv_file("/path/to/cal.tsv")
    test_all_corp_actual() 
    #print("Formula Engine created successfully.")
    #print("Use FormulaEngine.from_tsv_file(path_to_cal_tsv) to initialize.")