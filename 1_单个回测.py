from cta_api.base import BacktestConfig
from cta_api.engine import BacktestEngine
import config as global_config # 仍然可以读取 config.py 作为默认值

def main():
    symbol = getattr(global_config, "single_symbol", global_config.symbol_list[0])
    if getattr(global_config, "signal_name_list", None):
        default_factor = global_config.signal_name_list[0]
    else:
        default_factor = "sma"
    factor = getattr(global_config, "single_factor", default_factor)
    para_cfg = getattr(global_config, "single_para", None)
    if para_cfg is None:
        cfg_para = getattr(global_config, "para", [])
        if isinstance(cfg_para, list) and cfg_para:
            first = cfg_para[0]
            if isinstance(first, (list, tuple)):
                para_list = list(first)
            else:
                para_list = [first]
        else:
            para_list = []
    else:
        para_list = para_cfg
    start = getattr(global_config, "single_start", global_config.date_start)
    end = getattr(global_config, "single_end", global_config.date_end)
    if getattr(global_config, "rule_type_list", None):
        default_rule = global_config.rule_type_list[0]
    else:
        default_rule = "1H"
    rule_type = getattr(global_config, "single_rule_type", default_rule)

    # 1. 初始化配置
    # 优先使用命令行参数，其次使用 config.py，最后使用默认值
    cfg = BacktestConfig(
        c_rate=global_config.c_rate,
        slippage=global_config.slippage,
        leverage_rate=global_config.leverage_rate,
        min_margin_ratio=global_config.min_margin_ratio,
        proportion=global_config.proportion
    )
    
    engine = BacktestEngine(cfg)
    
    print(f"Starting Backtest: {symbol} | {factor} | {para_list}")
    engine.run_backtest(
        symbol=symbol,
        factor_name=factor,
        para=para_list,
        rule_type=rule_type,
        start_date=start,
        end_date=end,
        show_chart=True
    )

if __name__ == "__main__":
    main()
