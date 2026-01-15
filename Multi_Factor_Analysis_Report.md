# Multi-Factor Analysis Report: momentum.macd

## 1. Overview
- Symbol: BTC-USDT
- Date Range: 2023-01-01 to 2024-01-01
- Parameter Space Size: 48

## 2. Top Performance Statistics
- Max Sharpe: -4.4000
- Top 30% Threshold: -5.5600

## 3. Parameter Sensitivity
Correlation of parameters with Sharpe Ratio:
```
fast      0.367714
slow     -0.004748
signal    0.708294
```

## 4. PCA Analysis (Dimensionality Reduction)
Explained Variance Ratio: [0.49021678 0.32349053]

Principal Components:
```
         fast      slow    signal
PC1 -0.683444  0.687920  0.244275
PC2  0.192407 -0.153039  0.969308
```

Interpretation: High weights indicate direction of maximum variance in the successful parameter set.
