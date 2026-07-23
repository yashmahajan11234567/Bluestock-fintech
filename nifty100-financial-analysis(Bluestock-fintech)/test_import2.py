import sys
sys.path.insert(0, 'src')
try:
    import screener.engine
    print('Import succeeded')
except Exception as e:
    print('Import failed:', e)
    import screener
    print('Import succeeded')
except Exception as e:
    print('Import failed:', e)
    import traceback
    traceback.print_exc()
