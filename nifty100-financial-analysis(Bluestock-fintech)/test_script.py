import sys
sys.path.insert(0, 'src')
import screener as s
print('Testing imports...')
print('load_screener_data:', hasattr(s, 'load_screener_data'))
print('run_preset_screener:', hasattr(s, 'run_preset_screener'))
print('compute_composite_score:', hasattr(s, 'compute_composite_score'))
print('write_screener_output:', hasattr(s, 'write_screener_output'))
