import os
import sys
import importlib.util
import json
import inspect

def scan_factors(root_dir):
    factors_info = []
    
    # Add root dir to sys.path to allow imports
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    factors_dir = os.path.join(root_dir, 'factors')
    
    for root, dirs, files in os.walk(factors_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                module_name = os.path.splitext(rel_path)[0].replace(os.sep, '.')
                
                try:
                    # Dynamic import
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Extract info
                    doc = inspect.getdoc(module)
                    description = doc.strip().split('\n')[0] if doc else "No description available"
                    
                    param_count = 0
                    if hasattr(module, 'para_list'):
                        params = module.para_list()
                        if params and len(params) > 0:
                            param_count = len(params[0])
                    
                    # Calculate import path for engine (remove 'factors.' prefix)
                    import_path = module_name
                    if import_path.startswith('factors.'):
                        import_path = import_path[8:]
                        
                    factor_info = {
                        'name': file[:-3], # Display name
                        'import_path': import_path, # For engine
                        'path': rel_path,
                        'category': os.path.basename(root),
                        'description': description,
                        'param_count': param_count
                    }
                    factors_info.append(factor_info)
                    
                except Exception as e:
                    print(f"Error processing {rel_path}: {e}")

    return factors_info

if __name__ == "__main__":
    current_dir = os.getcwd()
    factors = scan_factors(current_dir)
    
    with open('factor_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(factors, f, ensure_ascii=False, indent=2)
    
    print(f"Scanned {len(factors)} factors. Saved to factor_metadata.json")
