#!/usr/bin/env python3
"""
因子规范性检查脚本
检查内容:
1. 是否可以导入
2. 是否包含 signal 函数
3. 是否包含 para_list 函数 (可选，但推荐)
4. signal 函数签名是否符合规范
"""

import sys
import os
import importlib
import inspect
from pathlib import Path

# 添加项目根目录到路径
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

def get_all_factors():
    """获取所有因子名称"""
    factors_path = Path(root_path) / "factors"
    factor_list = []
    
    # 遍历所有子目录
    for category in factors_path.iterdir():
        if category.is_dir() and not category.name.startswith('__') and category.name not in ['__pycache__', '.DS_Store']:
            for factor_file in category.glob("*.py"):
                if factor_file.name != "__init__.py":
                    factor_list.append(f"{category.name}.{factor_file.stem}")
    
    # 添加根目录下的因子
    for factor_file in factors_path.glob("*.py"):
        if factor_file.name not in ["__init__.py", "STRATEGIES_OVERVIEW.md", ".DS_Store"]:
            factor_list.append(factor_file.stem)
    
    return sorted(factor_list)

def check_factor(factor_name):
    """检查单个因子"""
    try:
        if "." in factor_name:
            mod_name = f"factors.{factor_name}"
        else:
            mod_name = f"factors.{factor_name}"
        
        mod = importlib.import_module(mod_name)
        
        issues = []
        
        # 检查 signal 函数
        if not hasattr(mod, 'signal'):
            issues.append("缺少 signal 函数")
        else:
            # 检查参数
            sig = inspect.signature(mod.signal)
            params = list(sig.parameters.keys())
            if 'df' not in params:
                issues.append("signal 函数缺少 'df' 参数")
            if 'para' not in params:
                issues.append("signal 函数缺少 'para' 参数")
        
        # 检查 para_list 函数
        if not hasattr(mod, 'para_list'):
            # issues.append("缺少 para_list 函数 (警告)")
            pass
            
        return issues
        
    except Exception as e:
        return [f"导入失败: {str(e)}"]

def main():
    print("开始检查因子规范性...")
    factors = get_all_factors()
    print(f"找到 {len(factors)} 个因子")
    
    problem_factors = {}
    
    for factor in factors:
        issues = check_factor(factor)
        if issues:
            problem_factors[factor] = issues
            print(f"❌ {factor}: {', '.join(issues)}")
        else:
            # print(f"✅ {factor}")
            pass
            
    print("-" * 50)
    print(f"检查完成。发现 {len(problem_factors)} 个问题因子。")
    
    if problem_factors:
        print("\n问题列表:")
        for factor, issues in problem_factors.items():
            print(f"{factor}: {issues}")

if __name__ == "__main__":
    main()
