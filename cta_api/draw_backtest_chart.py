import os
import platform
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot
from plotly.subplots import make_subplots


def draw_backtest_chart(df, trade, path='./pic.html', show=True, factor_col_name=None, chart_title='', metrics=None):
    """
    绘制统一的回测图表（适配所有因子）

    布局说明：
    - Row 1: K线图 + 买卖点标记 + 因子(主图overlay) (Height: 50%)
    - Row 2: 成交量 (Height: 15%)
    - Row 3: 资金曲线 + 因子(副图) (Height: 20%)
    - Row 4: 回撤曲线 (Height: 15%)

    :param df: 包含资金曲线和数据的 DataFrame
    :param trade: 每笔交易 DataFrame
    :param path: 保存路径
    :param show: 是否显示图表
    :param factor_col_name: 因子列名（可选）
    :param chart_title: 图表标题
    :param metrics: 回测指标 (DataFrame or Series)
    :return:
    """
    if trade is None or trade.empty:
        print("警告: 无交易数据，无法生成图表")
        return

    # 0. 数据预处理
    df = df.copy()
    g = trade.copy()
    
    # 计算回撤曲线
    if 'equity_curve' in df.columns:
        df['max2here'] = df['equity_curve'].expanding().max()
        df['dd2here'] = df['equity_curve'] / df['max2here'] - 1
    else:
        df['dd2here'] = 0

    # 1. 识别 factor_ 列
    factor_cols = [c for c in df.columns if c.startswith('factor_')]

    # 2. 准备标记点
    mark_point_list = []
    for i in g.index:
        buy_time = i
        sell_time = g.loc[i, 'end_bar']
        signal = g.loc[i, 'signal']
        
        # 获取开仓时刻的 High/Low
        open_high = df.loc[df['candle_begin_time'] == buy_time, 'high'].iloc[0]
        open_low = df.loc[df['candle_begin_time'] == buy_time, 'low'].iloc[0]
        
        # 获取平仓时刻的 High/Low
        close_high = df.loc[df['candle_begin_time'] == sell_time, 'high'].iloc[0]
        close_low = df.loc[df['candle_begin_time'] == sell_time, 'low'].iloc[0]

        # --- 开仓标记 ---
        if signal == 1: # 开多 (Green Arrow Up)
            mark_point_list.append({
                'x': buy_time,
                'y': open_low,
                'showarrow': True,
                'text': '',
                'arrowhead': 2,
                'arrowsize': 1.5,
                'arrowwidth': 2,
                'arrowcolor': '#00C853', # Green
                'ax': 0,
                'ay': 25, # Tail below
                'standoff': 4,
            })
        elif signal == -1: # 开空 (Red Arrow Down)
             mark_point_list.append({
                'x': buy_time,
                'y': open_high,
                'showarrow': True,
                'text': '',
                'arrowhead': 2,
                'arrowsize': 1.5,
                'arrowwidth': 2,
                'arrowcolor': '#D50000', # Red
                'ax': 0,
                'ay': -25, # Tail above
                'standoff': 4,
            })

        # --- 平仓标记 ---
        # 简化平仓标记：使用灰色小箭头或点
        if signal == 1: # 平多 (Close Long -> Sell)
            mark_point_list.append({
                'x': sell_time,
                'y': close_high,
                'showarrow': True,
                'text': '',
                'arrowhead': 3, # Different style
                'arrowsize': 1,
                'arrowwidth': 1.5,
                'arrowcolor': '#757575', # Grey
                'ax': 0,
                'ay': -15, 
                'standoff': 4,
            })
        elif signal == -1: # 平空 (Close Short -> Buy)
             mark_point_list.append({
                'x': sell_time,
                'y': close_low,
                'showarrow': True,
                'text': '',
                'arrowhead': 3,
                'arrowsize': 1,
                'arrowwidth': 1.5,
                'arrowcolor': '#757575', # Grey
                'ax': 0,
                'ay': 15,
                'standoff': 4,
            })

    # --- 添加绩效指标展示 ---
    if metrics is not None:
        metrics_str = "<b>Strategy Metrics</b><br>" + "-"*20 + "<br>"
        
        # 统一转为 Series 迭代
        if isinstance(metrics, pd.DataFrame):
            # 取第一列
            series_data = metrics.iloc[:, 0]
        elif isinstance(metrics, pd.Series):
            series_data = metrics
        else:
            series_data = pd.Series()

        # 筛选关键指标 (如果指标太多，可以只显示核心的)
        # 这里显示所有传入的指标
        for k, v in series_data.items():
            # 格式化数值
            if isinstance(v, (int, float)):
                if '收益' in str(k) or '率' in str(k) or '撤' in str(k): # 假设包含这些词的可能是百分比或小数
                     # 尝试判断是否需要百分号 (根据量级)
                     # 简单起见，保留4位小数或直接转字符串
                     val_str = f"{v:.4f}"
                else:
                     val_str = f"{v:.4f}"
            else:
                val_str = str(v)
            
            # 对齐显示
            metrics_str += f"{k}: <b>{val_str}</b><br>"

        mark_point_list.append({
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1.01, # 移到右侧 Margin 区域
                    'y': 0.99, # 顶部对齐
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'text': metrics_str,
                    'showarrow': False,
                    'font': {'size': 12, 'family': 'Arial'},
                    'align': 'left',
                    'bgcolor': 'rgba(255, 255, 255, 0.9)',
                    'bordercolor': '#888',
                    'borderwidth': 1,
                    'borderpad': 6
                })

    # 3. 准备 Traces
    traces_to_add = [] # List of (trace, row, secondary_y)

    # Row 1: K线
    trace_candlestick = go.Candlestick(
        x=df['candle_begin_time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='K线',
        increasing_line_color='red',
        decreasing_line_color='green'
    )
    traces_to_add.append((trace_candlestick, 1, False))

    # Row 2: 成交量 (独立行)
    trace_volume = go.Bar(
        x=df['candle_begin_time'],
        y=df['volume'],
        name='成交量',
        marker=dict(color='rgba(158,202,225,0.8)')
    )
    traces_to_add.append((trace_volume, 2, False))

    # Row 3: 资金曲线
    trace_equity = go.Scatter(
        x=df['candle_begin_time'],
        y=df['equity_curve'],
        name='资金曲线',
        line=dict(color='#4682B4', width=2)
    )
    traces_to_add.append((trace_equity, 3, False))

    # Row 4: 回撤曲线
    trace_dd = go.Scatter(
        x=df['candle_begin_time'],
        y=df['dd2here'],
        name='回撤',
        line=dict(color='#D50000', width=1),
        fill='tozeroy',
        fillcolor='rgba(213,0,0,0.2)'
    )
    traces_to_add.append((trace_dd, 4, False))

    # 4. 处理因子 Trace
    has_row3_factor = False
    
    for col in factor_cols:
        # 判断因子是否应该画在主图 (简单的启发式规则：均值在价格范围内)
        mean_val = df[col].mean()
        mean_close = df['close'].mean()
        
        is_price_overlay = False
        if pd.notnull(mean_val) and pd.notnull(mean_close):
             if 0.1 * mean_close < mean_val < 10 * mean_close:
                 is_price_overlay = True
        
        # 特殊规则：如果名字包含 ema, ma, boll, price，强制主图
        lower_name = col.lower()
        if any(x in lower_name for x in ['ema', 'ma', 'boll', 'price']):
            is_price_overlay = True
        
        trace = go.Scatter(
            x=df['candle_begin_time'],
            y=df[col],
            name=col,
            line=dict(width=1.5)
        )
        
        if is_price_overlay:
            # 叠加在主图 (Row 1)
            traces_to_add.append((trace, 1, False))
        else:
            # 叠加在资金曲线图 (Row 3)，使用右轴
            traces_to_add.append((trace, 3, True))
            has_row3_factor = True

    # 5. 创建 Subplots
    # Row 1: K线 (0.50)
    # Row 2: Volume (0.15)
    # Row 3: Equity (0.20)
    # Row 4: Drawdown (0.15)
    row_heights = [0.50, 0.15, 0.20, 0.15]
    
    specs = [
        [{"secondary_y": False}], # Row 1
        [{"secondary_y": False}], # Row 2
        [{"secondary_y": True}],  # Row 3 (支持双轴)
        [{"secondary_y": False}]  # Row 4
    ]

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        specs=specs,
        row_heights=row_heights
    )

    # 6. 添加所有 Traces
    for trace, row, sec_y in traces_to_add:
        # 如果 spec 不支持 secondary_y 但代码传入了 True，会报错
        # Row 1, 2, 4 我们的 spec 都是 secondary_y=False
        # Row 3 是 True
        # 只有当 row=3 时才允许 sec_y=True
        if row != 3:
            sec_y = False 
        
        fig.add_trace(trace, row=row, col=1, secondary_y=sec_y)

    layout_updates = {
        'template': 'none',
        'hovermode': 'x unified',
        'width': 1600,
        'height': 1000, # 增加总高度
        'annotations': mark_point_list,
        'title': chart_title,
        'xaxis_rangeslider_visible': False,
        'plot_bgcolor': 'white',
        'font': {'family': 'Arial', 'size': 12},
        'margin': {'l': 50, 'r': 280, 't': 60, 'b': 40}, # 增加右边距，放置 Metrics
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        }
    }

    fig.update_xaxes(
        title='',
        showgrid=True
    )

    # Row 1 Axis Config (Price)
    fig.update_yaxes(title='价格', showgrid=True, row=1, col=1)

    # Row 2 Axis Config (Volume)
    fig.update_yaxes(title='成交量', showgrid=True, row=2, col=1)

    # Row 3 Axis Config (Equity)
    fig.update_yaxes(title='资金曲线', showgrid=True, secondary_y=False, row=3, col=1)
    if has_row3_factor:
        fig.update_yaxes(title='因子值', showgrid=True, secondary_y=True, row=3, col=1)
        
    # Row 4 Axis Config (Drawdown)
    fig.update_yaxes(title='回撤', showgrid=True, row=4, col=1)

    fig.update_layout(**layout_updates)

    # 添加 y轴类型切换按钮 (针对资金曲线 Row 3)
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(label="线性 y轴",
                         method="relayout",
                         args=[{"yaxis3.type": "linear"}]), # 注意这里是 yaxis3
                    dict(label="对数 y轴",
                         method="relayout",
                         args=[{"yaxis3.type": "log"}])
                ],
                direction="down",
                showactive=True,
                x=0.01,
                y=1.02,
                xanchor='left',
                yanchor='top'
            )
        ]
    )

    fig.write_html(path, auto_open=False, include_plotlyjs='cdn')

    if show:
        if platform.system() == 'Windows':
            os.system(f'start "" "{path}"')
        elif platform.system() == 'Darwin':
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
