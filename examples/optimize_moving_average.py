"""Example script for optimizing a moving average trading strategy."""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

# Add project root to path
project_root = str(Path(__file__).parent.parent.absolute())
print(f"Project root: {project_root}")
sys.path.append(project_root)

from integration import create_optimizer

def evaluate_moving_average_strategy(data: pd.DataFrame, params: dict) -> float:
    """
    Evaluate a moving average crossover strategy.
    
    Args:
        data: DataFrame with OHLCV data
        params: Strategy parameters
        
    Returns:
        Strategy performance metric (Sharpe ratio)
    """
    # Convert parameters to integers
    fast_period = int(params["fast_period"]["value"]) if isinstance(params["fast_period"], dict) else int(params["fast_period"])
    slow_period = int(params["slow_period"]["value"]) if isinstance(params["slow_period"], dict) else int(params["slow_period"])
    
    # Ensure fast period is less than slow period and we have enough data
    if fast_period >= slow_period or len(data) < slow_period + 20:  # Need extra data for returns
        return float('-inf')
    
    # Calculate moving averages
    fast_ma = data["close"].rolling(window=fast_period).mean()
    slow_ma = data["close"].rolling(window=slow_period).mean()
    
    # Drop initial NaN values
    valid_idx = slow_ma.dropna().index
    fast_ma = fast_ma[valid_idx]
    slow_ma = slow_ma[valid_idx]
    
    # Ensure we have enough data points after dropping NaNs
    if len(fast_ma) < 20:  # Need at least 20 data points for meaningful statistics
        return float('-inf')
    
    # Generate signals
    signals = pd.Series(0, index=valid_idx)
    signals[fast_ma > slow_ma] = 1  # Long when fast MA crosses above slow MA
    signals[fast_ma < slow_ma] = -1  # Short when fast MA crosses below slow MA
    
    # Calculate returns
    daily_returns = data.loc[valid_idx, "close"].pct_change()
    strategy_returns = signals.shift(1) * daily_returns
    
    # Drop NaN values
    strategy_returns = strategy_returns.dropna()
    
    # Calculate Sharpe ratio (handle edge cases)
    if len(strategy_returns) < 20 or strategy_returns.std() == 0:
        return float('-inf')
        
    sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std()
    
    # Handle invalid values
    if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
        return float('-inf')
        
    return float(sharpe_ratio)

def main():
    """Run the optimization example."""
    # Get paths
    config_path = os.path.join(project_root, "config", "moving_average_config.json")
    data_path = os.path.join(project_root, "examples", "data", "sample_data.csv")
    output_dir = os.path.join(project_root, "examples", "results")
    
    print(f"Config path: {config_path}")
    print(f"Config path exists: {os.path.exists(config_path)}")
    print(f"Data path: {data_path}")
    print(f"Data path exists: {os.path.exists(data_path)}")
    print()
    
    # Create optimizer
    optimizer = create_optimizer(
        config_path=config_path,
        data_path=data_path,
        strategy_evaluator=evaluate_moving_average_strategy,
        output_dir=output_dir
    )
    
    # Run optimization
    optimizer.optimize()
    
    # Get best parameters
    best_params = optimizer.get_best_parameters()
    print("\nBest parameters found:", best_params)

if __name__ == "__main__":
    main()
