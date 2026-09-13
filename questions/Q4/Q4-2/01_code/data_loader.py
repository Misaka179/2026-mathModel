"""
Data loader for Q2: Load attachments and validate data quality
Author: Role B
Date: 2026-09-11
"""

import pandas as pd
import numpy as np
from pathlib import Path

class DataLoader:
    """Load and validate data from attachments 1 and 2"""

    def __init__(self, base_path=None):
        """
        Initialize data loader.
        Auto-detect path to attachments from script file location.
        """
        if base_path is None:
            # Use path relative to this script file
            # From Q4-2/01_code/data_loader.py up 4 levels to project root
            from pathlib import Path
            script_dir = Path(__file__).parent.absolute()
            attachment_path = script_dir / '../../../../C题/附件'

            if attachment_path.exists():
                self.base_path = str(attachment_path)
            else:
                raise FileNotFoundError(f"Cannot find attachments at: {attachment_path}")
        else:
            self.base_path = base_path

        self.price = None
        self.load_real = None
        self.pv_real = None
        self.dates = None

    def load_all(self):
        """Load all required data files"""
        self.load_price()
        self.load_load_pv()
        self.validate_all()
        return self.price, self.load_real, self.pv_real

    def load_price(self):
        """Load price from attachment 1 (144 points)"""
        file_path = f"{self.base_path}/附件1.xlsx"
        df = pd.read_excel(file_path)
        # Column 1 is price (元/kWh) - using index due to encoding issues
        self.price = df.iloc[:, 1].values
        assert len(self.price) == 144, f"Price must have 144 points, got {len(self.price)}"
        print(f"[OK] Price loaded: {len(self.price)} points, range [{self.price.min():.4f}, {self.price.max():.4f}] yuan/kWh")
        return self.price

    def load_load_pv(self):
        """Load real load and PV from attachment 2 (wide format: 365 days × 144 points)"""
        file_path = f"{self.base_path}/附件2.xlsx"

        # Load小区负载 (kW)
        df_load = pd.read_excel(file_path, sheet_name='小区负载')
        # First column is date, columns 2-145 are time points
        self.load_real = df_load.iloc[:, 1:145].values  # 365 × 144

        # Load光伏发电实际功率 (kW)
        df_pv = pd.read_excel(file_path, sheet_name='光伏发电实际功率')
        self.pv_real = df_pv.iloc[:, 1:145].values  # 365 × 144

        # Store dates for reference
        self.dates = pd.to_datetime(df_load.iloc[:, 0])

        print(f"[OK] Load data loaded: {self.load_real.shape} (days x time points)")
        print(f"[OK] PV data loaded: {self.pv_real.shape} (days x time points)")
        print(f"[OK] Date range: {self.dates.min()} to {self.dates.max()}")

        return self.load_real, self.pv_real

    def validate_all(self):
        """Validate input data quality (V0 level checks)"""
        errors = []

        # Check 1: Dimensions
        if self.price.shape != (144,):
            errors.append(f"Price must be 144 points, got {self.price.shape}")
        if self.load_real.shape != (365, 144):
            errors.append(f"Load must be 365×144, got {self.load_real.shape}")
        if self.pv_real.shape != (365, 144):
            errors.append(f"PV must be 365×144, got {self.pv_real.shape}")

        # Check 2: No missing values
        if np.isnan(self.price).any():
            errors.append("Price has NaN values")
        if np.isnan(self.load_real).any():
            errors.append("Load has NaN values")
        if np.isnan(self.pv_real).any():
            errors.append("PV has NaN values")

        # Check 3: Value ranges
        if not (0 <= self.price.min() and self.price.max() <= 10):
            errors.append(f"Price out of reasonable range [0, 10]: [{self.price.min()}, {self.price.max()}]")
        if (self.load_real < 0).any():
            errors.append("Load has negative values")
        if (self.pv_real < 0).any():
            errors.append("PV has negative values")

        # Check 4: Q2 planning period (Feb 1 to Dec 31 = 334 days)
        feb1_idx = (self.dates >= '2025-02-01').argmax()
        dec31_idx = (self.dates <= '2025-12-31').sum() - 1  # Convert count to index
        planning_days = dec31_idx - feb1_idx + 1  # +1 because inclusive range

        if planning_days != 334:
            errors.append(f"Q2 planning period should be 334 days, got {planning_days}")

        if errors:
            raise ValueError("Data validation failed:\n" + "\n".join(errors))

        print("\n=== Data Validation Passed ===")
        print(f"[OK] No missing values")
        print(f"[OK] No negative values")
        print(f"[OK] Dimensions correct")
        print(f"[OK] Q2 planning period: {planning_days} days (2025-02-01 to 2025-12-31)")
        print(f"[OK] Load range: [{self.load_real.min():.1f}, {self.load_real.max():.1f}] kW")
        print(f"[OK] PV range: [{self.pv_real.min():.1f}, {self.pv_real.max():.1f}] kW")

    def get_planning_period(self):
        """Get indices for Q2 planning period (Feb 1 - Dec 31, 2025)"""
        feb1_idx = (self.dates >= '2025-02-01').argmax()
        dec31_idx = (self.dates <= '2025-12-31').sum() - 1  # Convert count to index
        return feb1_idx, dec31_idx

    def get_specified_days(self):
        """Get indices for the 4 specified days in results"""
        specified_dates = [
            '2025-03-20',  # Spring equinox
            '2025-06-21',  # Summer solstice
            '2025-09-23',  # Autumn equinox
            '2025-12-21',  # Winter solstice
        ]
        indices = []
        for date_str in specified_dates:
            idx = (self.dates == date_str).argmax()
            if not (self.dates == date_str).any():
                raise ValueError(f"Specified date {date_str} not found in data")
            indices.append(idx)
        return indices, specified_dates


if __name__ == "__main__":
    # Test data loading
    loader = DataLoader()
    price, load_real, pv_real = loader.load_all()

    feb1_idx, dec31_idx = loader.get_planning_period()
    print(f"\nPlanning period indices: [{feb1_idx}, {dec31_idx})")

    spec_indices, spec_dates = loader.get_specified_days()
    print(f"\nSpecified days:")
    for idx, date in zip(spec_indices, spec_dates):
        print(f"  {date}: index {idx}")
