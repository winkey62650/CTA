import streamlit as st
import pandas as pd
import os
import sys
import importlib
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Add root to path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)

from cta_api.engine import BacktestEngine
from cta_api.base import BacktestConfig
import config as global_config
from cta_api.factor_scanner import scan_factors

st.set_page_config(page_title="CTA Parameter Plain Viewer", layout="wide")

@st.cache_data
def load_factors():
    return scan_factors(current_dir)

factors_info = load_factors()
factors_dict = {f['name']: f for f in factors_info}
sorted_factor_names = sorted(factors_dict.keys())

st.title("因子参数平原查看器 (Parameter Plain Viewer)")

# Sidebar
st.sidebar.header("配置")
selected_factor_name = st.sidebar.selectbox("选择因子", sorted_factor_names)
selected_symbol = st.sidebar.text_input("交易对", "BTC-USDT")
rule_type = st.sidebar.selectbox("周期", ["1H", "4H", "15M", "1D"], index=0)

start_date = st.sidebar.date_input("开始日期", datetime(2021, 1, 1))
end_date = st.sidebar.date_input("结束日期", datetime(2025, 1, 1))

# Factor Details
factor_data = factors_dict[selected_factor_name]
st.markdown(f"### 因子: {factor_data['name']}")
st.markdown(f"**描述**: {factor_data['description']}")
st.markdown(f"**参数数量**: {factor_data['param_count']}")

# Parameter Configuration
st.sidebar.subheader("参数范围设置")

params_config = []
for i in range(factor_data['param_count']):
    st.sidebar.markdown(f"**参数 {i+1}**")
    p_start = st.sidebar.number_input(f"Param {i+1} Start", value=10, key=f"p{i}_start")
    p_end = st.sidebar.number_input(f"Param {i+1} End", value=100, key=f"p{i}_end")
    p_step = st.sidebar.number_input(f"Param {i+1} Step", value=10, key=f"p{i}_step")
    
    # Generate range
    if p_step == 0: p_step = 1
    p_range = list(range(int(p_start), int(p_end) + 1, int(p_step)))
    params_config.append(p_range)

# Run Button
if st.button("开始分析 (Run Analysis)"):
    if factor_data['param_count'] == 0:
        st.error("此因子没有参数，无法进行参数平原分析。")
    else:
        # Prepare Engine
        cfg = BacktestConfig(
            c_rate=global_config.c_rate,
            slippage=global_config.slippage,
            leverage_rate=global_config.leverage_rate,
            min_margin_ratio=global_config.min_margin_ratio,
            proportion=global_config.proportion
        )
        engine = BacktestEngine(cfg)
        
        # Generate combinations
        import itertools
        combinations = list(itertools.product(*params_config))
        total_runs = len(combinations)
        
        if total_runs > 500:
            st.warning(f"即将运行 {total_runs} 次回测，可能需要较长时间。")
        
        st.info(f"正在运行 {total_runs} 次回测...")
        
        progress_bar = st.progress(0)
        results = []
        
        start_time_str = start_date.strftime("%Y-%m-%d")
        end_time_str = end_date.strftime("%Y-%m-%d")

        for idx, param_set in enumerate(combinations):
            try:
                # Run backtest
                # Convert tuple to list for the engine
                para_list = list(param_set)
                
                df, metrics = engine.run_backtest(
                    symbol=selected_symbol,
                    factor_name=factor_data['import_path'],
                    para=para_list,
                    rule_type=rule_type,
                    start_date=start_time_str,
                    end_date=end_time_str,
                    show_chart=False
                )
                
                if metrics is not None:
                    res = {
                        'para': str(para_list),
                        'return': metrics.loc['年化收益', 0],
                        'sharpe': metrics.loc['夏普比率', 0],
                        'max_dd': metrics.loc['最大回撤', 0],
                        'calmar': metrics.loc['年化收益/回撤比', 0]
                    }
                    # Add individual params for plotting
                    for p_i, p_val in enumerate(para_list):
                        res[f'p{p_i+1}'] = p_val
                        
                    results.append(res)
            except Exception as e:
                print(f"Error: {e}")
            
            progress_bar.progress((idx + 1) / total_runs)
            
        progress_bar.empty()
        
        if not results:
            st.error("没有生成结果。请检查数据或参数。")
        else:
            df_res = pd.DataFrame(results)
            st.success("分析完成！")
            
            st.subheader("分析结果")
            st.dataframe(df_res)
            
            # Visualization
            metric_to_plot = st.selectbox("选择指标", ['sharpe', 'return', 'max_dd', 'calmar'])
            
            if factor_data['param_count'] == 1:
                # Line Chart
                fig = px.line(df_res, x='p1', y=metric_to_plot, markers=True, 
                              title=f"单参数敏感性分析: {metric_to_plot}")
                st.plotly_chart(fig, use_container_width=True)
                
            elif factor_data['param_count'] == 2:
                # Heatmap
                # Pivot data
                pivot_df = df_res.pivot(index='p2', columns='p1', values=metric_to_plot)
                
                fig = go.Figure(data=go.Heatmap(
                    z=pivot_df.values,
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    colorscale='Viridis',
                    colorbar=dict(title=metric_to_plot)
                ))
                fig.update_layout(
                    title=f"双参数热力图: {metric_to_plot}",
                    xaxis_title="Parameter 1",
                    yaxis_title="Parameter 2"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("3个或更多参数的可视化暂只支持前两个参数的热力图 (固定其他参数) 或查看原始数据表格。")
                if 'p2' in df_res.columns:
                     # Attempt to plot p1 vs p2 and average the metric if multiple values exist
                    pivot_df = df_res.groupby(['p1', 'p2'])[metric_to_plot].mean().unstack()
                    fig = go.Figure(data=go.Heatmap(
                        z=pivot_df.values,
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        colorscale='Viridis'
                    ))
                    fig.update_layout(title=f"前两个参数热力图 (聚合): {metric_to_plot}")
                    st.plotly_chart(fig, use_container_width=True)

