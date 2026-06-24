import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
sys.path.append(".")
from ai_lab_comm.log_util import log

class FinancialMetricsCalculator:
    """
    A calculator class that loads financial metrics calculation configurations from a YAML file,
    parses the rules, and applies them to line items retrieved from financials.ai API
    to generate specific financial metric values.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the calculator with a configuration file.
        
        Args:
            config_path: Path to the YAML configuration file. If None, looks for default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "financial_metrics_config.yaml"
        
        self.config_path = config_path
        self.metrics_config = self._load_config()
        self.metrics_lookup_table = self._build_metrics_lookup()  # 构建用于快速查找的索引
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the financial metrics configuration from YAML file.
        
        Returns:
            Dictionary containing the configuration data
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            log.error(f"Configuration file not found at {self.config_path}")
            log.info("Using default configuration...")
            return None
        except yaml.YAMLError as e:
            log.error(f"Error parsing YAML configuration: {e}")
            return None
    
    def _build_metrics_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a lookup dictionary for fast metric access based on the loaded config.
        
        Returns:
            Dictionary mapping metric IDs to their configurations
        """
        lookup = {}
        
        if self.metrics_config and 'financial_metrics' in self.metrics_config:
            for metric in self.metrics_config['financial_metrics']:
                if 'id' in metric:
                    lookup[metric['id']] = metric
                    log.info(f"Loaded metric: {metric['id']}, {metric}") # 
        return lookup
    
    def calculate_metric(self, metric_name: str, line_items: Dict[str, float]) -> Optional[float]:
        """
        Calculate a specific financial metric based on the provided line items.
        
        Args:
            metric_name: Name of the metric to calculate
            line_items: Dictionary of line item names and their values
            
        Returns:
            Calculated metric value or None if calculation fails
        """
        # Find the metric configuration using the lookup
        metric_config = self.metrics_lookup_table.get(metric_name)
        
        if not metric_config:
            print(f"Metric '{metric_name}' not found in configuration")
            return None
        
        formula = metric_config['formula']

        # Extract dependencies from the formula (this is a simple implementation)
        # In a more robust implementation, dependencies should be explicitly defined in the config
        dependencies = self._extract_dependencies_from_formula(formula)
        
        # Check if all dependencies are available in line_items
        missing_deps = [dep for dep in dependencies if dep not in line_items]
        if missing_deps:
            print(f"Missing dependencies for '{metric_name}': {missing_deps}")
            return None
        
        # Replace variable names in the formula with actual values
        try:
            # Create a safe evaluation environment
            safe_dict = {}
            for dep in dependencies:
                safe_dict[dep] = line_items[dep]
            
            # Evaluate the formula
            result = eval(formula, {"__builtins__": {}}, safe_dict)
            log.info(f"Calculated '{metric_name}'': {formula}, {safe_dict}, result is {result}")
            return result
        except ZeroDivisionError:
            print(f"Division by zero error when calculating '{metric_name}'")
            return None
        except Exception as e:
            print(f"Error calculating '{metric_name}': {e}")
            return None
    
    def _extract_dependencies_from_formula(self, formula: str) -> List[str]:
        """
        Extract dependencies from a formula string.
        This is a basic implementation that identifies uppercase words in the formula.
        
        Args:
            formula: Formula string to extract dependencies from
            
        Returns:
            List of dependency names
        """
        import re
        # Find all uppercase words in the formula
        dependencies = re.findall(r'[A-Z_][A-Z0-9_]*', formula)
        return list(set(dependencies))  # Return unique dependencies
    
    def _find_metric_config(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Find the configuration for a specific metric.
        
        Args:
            metric_name: Name of the metric to find
            
        Returns:
            Metric configuration dictionary or None if not found
        """
        return self.metrics_lookup_table.get(metric_name)
    
    def calculate_all_metrics(self, line_items: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate all available metrics based on the provided line items.
        
        Args:
            line_items: Dictionary of line item names and their values
            
        Returns:
            Dictionary with metric names as keys and calculated values as values
        """
        results = {}
        
        for metric_id, metric_config in self.metrics_lookup_table.items():
            value = self.calculate_metric(metric_id, line_items)
            if value is not None:
                results[metric_id] = value
        
        return results
    
    def get_available_metrics(self) -> List[str]:
        """
        Get a list of all available metrics in the configuration.
        
        Returns:
            List of available metric names
        """
        return list(self.metrics_lookup_table.keys())
    
    def get_metric_info(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific metric.
        
        Args:
            metric_name: Name of the metric to get info for
            
        Returns:
            Dictionary with metric information or None if not found
        """
        metric_config = self.metrics_lookup_table.get(metric_name)
        if metric_config:
            # Add the metric name to the config
            result = metric_config.copy()
            result['id'] = metric_name
            return result
        return None
    
    def get_metrics_by_category(self, category: str) -> List[str]:
        """
        Get all metrics belonging to a specific category.
        
        Args:
            category: Category name to filter metrics by
            
        Returns:
            List of metric names in the specified category
        """
        metrics = []
        for metric_id, metric_config in self.metrics_lookup_table.items():
            if metric_config.get('category', '').lower() == category.lower():
                metrics.append(metric_id)
        return metrics
    
    def validate_line_items(self, line_items: Dict[str, float], metric_name: str) -> Dict[str, bool]:
        """
        Validate which dependencies for a metric are available in the line items.
        
        Args:
            line_items: Dictionary of line item names and their values
            metric_name: Name of the metric to validate against
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        metric_config = self.metrics_lookup_table.get(metric_name)
        if not metric_config:
            return {}
        
        formula = metric_config['formula']
        dependencies = self._extract_dependencies_from_formula(formula)
        
        validation_results = {}
        
        for dep in dependencies:
            validation_results[dep] = dep in line_items
        
        return validation_results


class FinancialMetricsAPIAdapter:
    """
    Adapter class to work with the financial_metrics_api.py to fetch line items
    and apply calculations using the FinancialMetricsCalculator.
    """
    
    def __init__(self, calculator: FinancialMetricsCalculator):
        """
        Initialize the adapter with a calculator instance.
        
        Args:
            calculator: An instance of FinancialMetricsCalculator
        """
        self.calculator = calculator
    
    def calculate_from_api_data(self, api_response: Dict[str, Any], ticker: str) -> Dict[str, float]:
        """
        Calculate financial metrics from API response data.
        
        Args:
            api_response: Response from financials.ai API
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with calculated metric values
        """
        # Extract line items from the API response
        line_items = self._extract_line_items(api_response, ticker)
        
        # Calculate all metrics using the calculator
        results = self.calculator.calculate_all_metrics(line_items)
        
        return results
    
    def _extract_line_items(self, api_response: Dict[str, Any], ticker: str) -> Dict[str, float]:
        """
        Extract line items from API response structure.
        
        Args:
            api_response: Response from financials.ai API
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with line item names and values
        """
        line_items = {}
        
        # Try different structures in the API response
        if ticker in api_response:
            ticker_data = api_response[ticker]
            
            # If the ticker data contains yearly data
            if isinstance(ticker_data, dict):
                # Look for the most recent year data
                if 'yearly' in ticker_data:
                    # Get the most recent year
                    most_recent_year = max(ticker_data['yearly'].keys()) if ticker_data['yearly'] else None
                    if most_recent_year:
                        year_data = ticker_data['yearly'][most_recent_year]
                        line_items.update(self._normalize_keys(year_data))
                elif isinstance(ticker_data, dict):
                    # Direct mapping
                    line_items.update(self._normalize_keys(ticker_data))
        
        return line_items
    
    def _normalize_keys(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize keys in the data dictionary to match expected line item names.
        
        Args:
            data: Dictionary with potentially inconsistent key naming
            
        Returns:
            Dictionary with normalized keys
        """
        normalized = {}
        
        for key, value in data.items():
            # Convert string numbers to floats if possible
            if isinstance(value, str):
                try:
                    value = float(value.replace(',', ''))  # Remove commas from numbers like '1,234.56'
                except ValueError:
                    continue  # Skip non-numeric strings
            
            if isinstance(value, (int, float)):
                # Normalize the key name to match expected format
                normalized_key = self._normalize_key_name(key)
                normalized[normalized_key] = float(value)
        
        return normalized
    
    def _normalize_key_name(self, key: str) -> str:
        """
        Normalize a key name to match expected format.
        
        Args:
            key: Original key name
            
        Returns:
            Normalized key name
        """
        # Common mappings to standardize key names
        key_mappings = {
            'revenue': 'REVENUES',
            'total_revenue': 'REVENUES',
            'sales': 'REVENUES',
            'net_income': 'NET_INCOME',
            'income': 'NET_INCOME',
            'net_profit': 'NET_INCOME',
            'gross_profit': 'GROSS_PROFIT',
            'operating_income': 'OPERATING_INCOME',
            'ebit': 'EBIT',
            'ebitda': 'EBITDA',
            'assets': 'ASSETS',
            'total_assets': 'ASSETS',
            'liabilities': 'LIABILITIES',
            'total_liabilities': 'TOTAL_LIABILITIES',
            'equity': 'STOCKHOLDERS_EQUITY',
            'shareholders_equity': 'STOCKHOLDERS_EQUITY',
            'stockholders_equity': 'STOCKHOLDERS_EQUITY',
            'current_assets': 'CURRENT_ASSETS',
            'current_liabilities': 'CURRENT_LIABILITIES',
            'long_term_debt': 'LONG_TERM_DEBT',
            'debt': 'LONG_TERM_DEBT',
            'interest_expense': 'INTEREST_EXPENSE',
            'cost_of_goods_sold': 'COST_OF_GOODS_AND_SERVICES_SOLD',
            'cogs': 'COST_OF_GOODS_AND_SERVICES_SOLD',
            'inventory': 'INVENTORY_AND_CONTRACT_COSTS_NOT_YET_RECOGNIZED_AS_REVENUE',
            'cash': 'CASH_AND_CASH_EQUIVALENTS_AT_CARRYING_VALUE',
            'cash_and_cash_equivalents': 'CASH_AND_CASH_EQUIVALENTS_AT_CARRYING_VALUE',
            'operating_cash_flow': 'OPERATING_CASH_FLOW',
            'capex': 'CAPITAL_EXPENDITURES',
            'capital_expenditures': 'CAPITAL_EXPENDITURES',
            'market_cap': 'MARKET_CAP',
            'book_value': 'BOOK_VALUE',
            'total_debt': 'TOTAL_DEBT',
            'cash_equivalents': 'CASH_EQUIVALENTS',
        }
        
        normalized_key = key.lower().replace(' ', '_').replace('-', '_')
        return key_mappings.get(normalized_key, key.upper())


# Example usage
if __name__ == "__main__":
    # Initialize the calculator
    calculator = FinancialMetricsCalculator()
    
    # Print available metrics
    print("Available metrics:")
    for metric in calculator.get_available_metrics():
        print(f"- {metric}")
    
    # Example line items (these would come from financials.ai API)
    sample_line_items = {
        "REVENUES": 1000000.0,
        "NET_INCOME": 100000.0,
        "CURRENT_ASSETS": 500000.0,
        "CURRENT_LIABILITIES": 200000.0,
        "STOCKHOLDERS_EQUITY": 600000.0,
        "LONG_TERM_DEBT": 150000.0,
        "COST_OF_GOODS_AND_SERVICES_SOLD": 600000.0,
        "OPERATING_INCOME": 200000.0,
        "ASSETS": 1200000.0,
        "TOTAL_LIABILITIES": 600000.0,
        "MARKET_CAP": 2000000.0,
        "EBITDA": 250000.0,
        "OPERATING_CASH_FLOW": 220000.0,
        "CAPITAL_EXPENDITURES": 50000.0,
        "CASH_EQUIVALENTS": 50000.0,
        "BOOK_VALUE": 600000.0,
        "TOTAL_DEBT": 200000.0
    }
    
    print("\nSample line items:", sample_line_items)
    
    # Calculate all metrics
    results = calculator.calculate_all_metrics(sample_line_items)
    print("\nCalculated metrics:")
    for metric, value in results.items():
        print(f"{metric}: {value:.4f}")
    
    # Calculate a specific metric
    print(f"\nEnterprise value: {calculator.calculate_metric('enterprise_value', sample_line_items):.4f}")
    print(f"P/E ratio: {calculator.calculate_metric('price_to_earnings_ratio', sample_line_items):.4f}")
    print(f"P/B ratio: {calculator.calculate_metric('price_to_book_ratio', sample_line_items):.4f}")
    
    # Get metric information
    print(f"\nEnterprise value info: {calculator.get_metric_info('enterprise_value')}")
    
    # Get metrics by category
    print(f"\nValuation metrics: {calculator.get_metrics_by_category('Valuation')}")