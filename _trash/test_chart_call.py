#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/winkey/Documents/Quant/CTA')

from cta_api.draw_backtest_chart import draw_backtest_chart
print('测试调用图表函数...')
draw_backtest_chart(
    df=None,
    trade=None,
    path='/Users/winkey/Documents/Quant/CTA/data/output/charts/test_simple.html',
    show=False,
    chart_title='简单测试',
    factor_col_name=None
)
print('完成')
