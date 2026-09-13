"""
Scenario construction using historical joint residuals
"""

import numpy as np
from typing import List, Tuple


class ScenarioBuilder:
    """Construct scenarios from historical joint residuals"""

    def __init__(self, load_real, pv_real, M=30):
        """
        Args:
            load_real: Real load data (365 x 144)
            pv_real: Real PV data (365 x 144)
            M: Number of scenarios to use (default 30)
        """
        self.load_real = load_real
        self.pv_real = pv_real
        self.M = M

    def forecast_load(self, day_d, method='same_weekday_35days'):
        """
        Forecast load for day d using only historical data before day d

        Method: Use same weekday from previous 35 days (at least 2 samples)
        If fewer than 2 samples, fall back to previous 7 days average
        """
        if day_d == 0:
            # No history, use global average of entire dataset
            return self.load_real.mean(axis=0)

        if day_d < 7:
            # Not enough history, use available days
            return self.load_real[:day_d].mean(axis=0)

        # Get weekday of day d (assuming day 0 is 2025-01-01, which is Wednesday)
        # Jan 1, 2025 is Wednesday (weekday=2)
        weekday_d = (2 + day_d) % 7  # 0=Mon, 1=Tue, ..., 6=Sun

        # Find same weekdays in previous 35 days (or available history)
        lookback = min(35, day_d)
        same_weekday_indices = []

        for i in range(day_d - lookback, day_d):
            weekday_i = (2 + i) % 7
            if weekday_i == weekday_d:
                same_weekday_indices.append(i)

        if len(same_weekday_indices) >= 2:
            # Use same weekday average
            return self.load_real[same_weekday_indices].mean(axis=0)
        else:
            # Fall back to previous 7 days average
            return self.load_real[day_d-7:day_d].mean(axis=0)

    def forecast_pv(self, day_d, method='recent_7days'):
        """
        Forecast PV for day d using only historical data before day d

        Method: Use previous 7 days average
        """
        if day_d == 0:
            # No history, use global average of entire dataset
            return self.pv_real.mean(axis=0)

        if day_d < 7:
            # Not enough history, use available days
            return self.pv_real[:day_d].mean(axis=0)

        return self.pv_real[day_d-7:day_d].mean(axis=0)

    def construct_scenarios(self, day_d) -> List[dict]:
        """
        Construct M scenarios for day d using historical joint residuals

        Returns:
            List of scenario dicts, each containing:
            - 'load': load scenario (144 points, kW)
            - 'pv': pv scenario (144 points, kW)
            - 'weight': scenario weight (1/M for equal weight)
        """
        # Step 1: Generate forecast for day d (using only data before day d)
        load_forecast_d = self.forecast_load(day_d)
        pv_forecast_d = self.forecast_pv(day_d)

        # Step 2: Get historical residuals from previous M days
        # Make sure we have enough history
        lookback = min(self.M, day_d)
        if lookback < self.M:
            print(f"Warning: Day {day_d} has only {lookback} historical days, using all available")

        scenarios = []

        for i in range(day_d - lookback, day_d):
            # Historical day i's forecast (using data before day i)
            load_forecast_i = self.forecast_load(i)
            pv_forecast_i = self.forecast_pv(i)

            # Historical residuals (same-day pairing preserves joint correlation)
            residual_load = self.load_real[i] - load_forecast_i
            residual_pv = self.pv_real[i] - pv_forecast_i

            # Generate scenario s: add historical residual to day d's forecast
            load_scenario = np.maximum(load_forecast_d + residual_load, 0)  # Truncate negative
            pv_scenario = np.maximum(pv_forecast_d + residual_pv, 0)  # Truncate negative

            scenarios.append({
                'load': load_scenario,
                'pv': pv_scenario,
                'weight': 1.0 / lookback,  # Equal weight
                'source_day': i
            })

        return scenarios

    def construct_scenarios_simple(self, day_d, num_scenarios=None):
        """
        Simplified scenario construction for testing
        Just use the last M days' actual values as scenarios
        """
        if num_scenarios is None:
            num_scenarios = self.M

        lookback = min(num_scenarios, day_d)
        scenarios = []

        for i in range(day_d - lookback, day_d):
            scenarios.append({
                'load': self.load_real[i],
                'pv': self.pv_real[i],
                'weight': 1.0 / lookback,
                'source_day': i
            })

        return scenarios


if __name__ == "__main__":
    # Test scenario construction
    from data_loader import DataLoader

    loader = DataLoader()
    price, load_real, pv_real = loader.load_all()

    builder = ScenarioBuilder(load_real, pv_real, M=30)

    # Test on day 60 (enough history)
    day_d = 60
    scenarios = builder.construct_scenarios(day_d)

    print(f"\n=== Scenario Construction Test (Day {day_d}) ===")
    print(f"Number of scenarios: {len(scenarios)}")
    print(f"Each scenario weight: {scenarios[0]['weight']:.4f}")
    print(f"Load scenario shape: {scenarios[0]['load'].shape}")
    print(f"PV scenario shape: {scenarios[0]['pv'].shape}")

    # Check total weight
    total_weight = sum(s['weight'] for s in scenarios)
    print(f"Total weight: {total_weight:.4f} (should be 1.0)")

    # Show scenario statistics
    load_means = [s['load'].mean() for s in scenarios]
    pv_means = [s['pv'].mean() for s in scenarios]
    print(f"\nLoad scenario means: min={min(load_means):.1f}, max={max(load_means):.1f} kW")
    print(f"PV scenario means: min={min(pv_means):.1f}, max={max(pv_means):.1f} kW")
