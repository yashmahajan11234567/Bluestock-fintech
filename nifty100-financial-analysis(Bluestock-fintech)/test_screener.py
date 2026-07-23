import sys
sys.path.insert(0, 'src')
try:
    import screener
    print('screener package imported, file:', screener.__file__)
except Exception as e:
    print('Failed to import screener:', e)
    import traceback
    traceback.print_exc()
