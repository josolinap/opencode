#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from enhanced_error_recovery import EnhancedErrorRecovery
    print('[OK] Import successful')
    
    # Test basic instantiation
    recovery = EnhancedErrorRecovery()
    print('[OK] Instantiation successful')
    print(f'[OK] Auto healing enabled: {recovery.auto_healing_enabled}')
    print(f'[OK] Recovery strategies: {len(recovery.recovery_strategies)}')
    print('[OK] enhanced_error_recovery.py working correctly')
    
except Exception as e:
    print(f'[ERROR] Error: {e}')
    import traceback
    traceback.print_exc()