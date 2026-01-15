import os
import sys
import importlib.util
import pandas as pd
import numpy as np
import traceback

# Add root to path
sys.path.append(os.getcwd())

def create_dummy_data(n=1000):
    dates = pd.date_range(start='2024-01-01', periods=n, freq='H')
    df = pd.DataFrame({
        'candle_begin_time': dates,
        'open': np.random.randn(n) * 10 + 100,
        'high': np.random.randn(n) * 10 + 110,
        'low': np.random.randn(n) * 10 + 90,
        'close': np.random.randn(n) * 10 + 100,
        'volume': np.random.randint(100, 1000, n)
    })
    # Make sure High is highest and Low is lowest
    df['high'] = df[['open', 'close', 'high']].max(axis=1) + 1
    df['low'] = df[['open', 'close', 'low']].min(axis=1) - 1
    return df

def check_factors(root_dir):
    factors_dir = os.path.join(root_dir, 'factors')
    results = []
    
    print(f"Scanning factors in {factors_dir}...\n")
    
    for root, dirs, files in os.walk(factors_dir):
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                module_name = os.path.splitext(rel_path)[0].replace(os.sep, '.')
                
                print(f"Checking {module_name}...", end=" ", flush=True)
                
                try:
                    # 1. Import
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module # Mock sys.modules for relative imports if any
                    spec.loader.exec_module(module)
                    
                    # 2. Check structure
                    has_signal = hasattr(module, 'signal')
                    has_para_list = hasattr(module, 'para_list')
                    
                    if not has_signal:
                        print("❌ Missing 'signal' function")
                        results.append({'name': module_name, 'status': 'Error', 'msg': "Missing 'signal' function"})
                        continue
                        
                    # 3. Get params
                    params = []
                    if has_para_list:
                        try:
                            params = module.para_list()
                        except Exception as e:
                            print(f"❌ para_list() error: {e}")
                            results.append({'name': module_name, 'status': 'Error', 'msg': f"para_list() error: {e}"})
                            continue
                    
                    # Use first param or default
                    test_para = params[0] if params and len(params) > 0 else []
                    
                    # 4. Run signal
                    df = create_dummy_data()
                    try:
                        # Try calling with standard arguments
                        # signal(df, para, proportion=1, leverage_rate=1)
                        # Some factors might have different signatures, but our standard is defined in BaseFactor
                        # We'll try the most common one.
                        
                        # Inspect signature just in case
                        import inspect
                        sig = inspect.signature(module.signal)
                        # print(sig)
                        
                        # If test_para is empty and function expects para, we might have issues if we don't provide it
                        # But let's try passing it.
                        
                        if test_para:
                             df_res = module.signal(df.copy(), para=test_para)
                        else:
                             # Try with default if possible, or pass empty list
                             df_res = module.signal(df.copy(), para=[])
                             
                        if 'signal' not in df_res.columns and 'signal_long' not in df_res.columns:
                             print("⚠️ No signal column generated")
                             results.append({'name': module_name, 'status': 'Warning', 'msg': "No signal column generated"})
                        else:
                             print("✅ OK")
                             results.append({'name': module_name, 'status': 'OK', 'msg': "Passed"})
                             
                    except Exception as e:
                        print(f"❌ Runtime Error: {e}")
                        # print(traceback.format_exc())
                        results.append({'name': module_name, 'status': 'Error', 'msg': f"Runtime Error: {e}"})

                except Exception as e:
                    print(f"❌ Import/Load Error: {e}")
                    results.append({'name': module_name, 'status': 'Error', 'msg': f"Import/Load Error: {e}"})
    
    print("\nSummary:")
    error_count = 0
    for res in results:
        if res['status'] == 'Error':
            print(f"- {res['name']}: {res['msg']}")
            error_count += 1
            
    print(f"\nTotal Errors: {error_count} / {len(results)}")

if __name__ == "__main__":
    check_factors(os.getcwd())
