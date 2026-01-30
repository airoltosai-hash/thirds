# automation/test/test_hts_window.py

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')
from test.window_inspector import print_windows_info

if __name__ == "__main__":
    print_windows_info()