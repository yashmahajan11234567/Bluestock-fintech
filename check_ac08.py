import time
import requests

tickers = ['TCS', 'RELIANCE', 'HDFCBANK', 'INFY', 'ICICIBANK']
all_ok = True

for ticker in tickers:
    start = time.time()
    try:
        r = requests.get(f'http://127.0.0.1:8003/api/v1/companies/{ticker}', timeout=5)
        elapsed = time.time() - start
        if r.status_code == 200:
            print(f'{ticker}: {elapsed:.3f} seconds')
            if elapsed >= 3.0:
                print(f'  WARNING: >= 3 seconds')
                all_ok = False
        else:
            print(f'{ticker}: HTTP {r.status_code}')
            all_ok = False
    except Exception as e:
        print(f'{ticker}: Error - {e}')
        all_ok = False

if all_ok:
    print('AC-08: PASS (all under 3 seconds)')
else:
    print('AC-08: FAIL (one or more over 3 seconds or error)')