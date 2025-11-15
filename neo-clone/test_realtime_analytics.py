#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from realtime_analytics import RealTimeAnalytics
    print('[OK] Import successful')
    
    # Test basic instantiation
    analytics = RealTimeAnalytics()
    print('[OK] RealTimeAnalytics instantiation successful')
    print(f'[OK] Alert callbacks: {len(analytics.alert_callbacks)}')
    print(f'[OK] Current metrics keys: {list(analytics.current_metrics.keys())}')
    
    # Test record_metric method
    analytics.record_metric('test_metric', 1.5, {'tag': 'test'})
    print('[OK] record_metric method working')
    
    # Test add_alert_callback method
    def test_callback(alert):
        pass
    analytics.add_alert_callback(test_callback)
    print('[OK] add_alert_callback method working')
    
    print('[OK] realtime_analytics.py working correctly')
    
except Exception as e:
    print(f'[ERROR] Error: {e}')
    import traceback
    traceback.print_exc()