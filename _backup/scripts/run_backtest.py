import os
import subprocess
from config import root_path

def run_fast_backview():
    p = subprocess.run(["python", os.path.join(root_path, "2_fast_backview.py")], capture_output=True, text=True)
    print(p.stdout)
    print(p.stderr)

if __name__ == "__main__":
    run_fast_backview()

