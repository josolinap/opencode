#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from smart_routing import SmartRouter, RoutingContext
    print('[OK] Import successful')
    
    # Test basic instantiation
    router = SmartRouter()
    print('[OK] SmartRouter instantiation successful')
    print(f'[OK] Models loaded: {len(router.models)}')
    print(f'[OK] Skills loaded: {len(router.skills)}')
    
    # Test RoutingContext
    context = RoutingContext(user_input="test input")
    print('[OK] RoutingContext instantiation successful')
    print('[OK] smart_routing.py working correctly')
    
except Exception as e:
    print(f'[ERROR] Error: {e}')
    import traceback
    traceback.print_exc()