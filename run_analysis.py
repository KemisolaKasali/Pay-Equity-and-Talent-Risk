"""Compatibility entry point for the original project script name.

The analysis is maintained in pay_equity_analysis.py.
"""

from pay_equity_analysis import PayEquityAnalysis
from pathlib import Path


if __name__ == "__main__":
    data_file = (
        Path(__file__).parent
        / "data"
        / "raw"
        / "BananaByte_Employee_Salary_090923 CleanedData_On_Python.csv"
    )
    PayEquityAnalysis(data_file).run()
