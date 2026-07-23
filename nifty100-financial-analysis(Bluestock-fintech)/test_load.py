import sys
import importlib.util
spec = importlib.util.spec_from_file_location('screener.engine', 'src/screener/engine.py')
module = importlib.util.module_from_spec(spec)
sys.modules['spec.name'] = module
try:
    spec.loader.exec_module(module)
    print('Module loaded successfully')
except Exception as e:
    print('Error loading module:', e)
    import traceback
    traceback.print_exc()
