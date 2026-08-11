import sys
import os
sys.path.insert(0, 'src')

# Import the actual function
from reports.portfolio_summary import _calculate_trend_arrow

print('Testing the actual _calculate_trend_arrow function from the implementation:')
print()

test_cases = [
    # (latest, previous, expected, description)
    (102, 100, '→', 'exactly +2%'),
    (98, 100, '→', 'exactly -2%'),
    (101, 100, '→', 'within +2%'),
    (99, 100, '→', 'within -2%'),
    (105, 100, '↑', 'greater than +2%'),
    (95, 100, '↓', 'less than -2%'),
    (None, 100, '→', 'latest is None'),
    (100, None, '→', 'previous is None'),
    (float('nan'), 100, '→', 'latest is NaN'),
    (100, float('nan'), '→', 'previous is NaN'),
    (0, 0, '→', 'both zero'),
    (50, 0, '↑', 'zero previous'),
    (-50, 0, '↓', 'zero previous negative'),
    (1.0001, 1, '→', 'within 0.01%'),
    (1.03, 1, '↑', 'greater than 2%'),
    (0.98, 1, '↓', 'less than -2%'),
]

all_passed = True
for latest, previous, expected, description in test_cases:
    try:
        result = _calculate_trend_arrow(latest, previous)
        passed = result == expected
        status = '✓' if passed else '✗'
        print(f'{status} ({latest}, {previous}) -> {result} (expected: {expected}) - {description}')
        if not passed:
            all_passed = False
    except Exception as e:
        print(f'✗ ({latest}, {previous}) -> ERROR: {e} - {description}')
        all_passed = False

print()
print('Overall test result:', 'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED')