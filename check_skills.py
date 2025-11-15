#!/usr/bin/env python3
import sys
import os
sys.path.append('neo-clone')

try:
    from skills import get_skills_manager
    sm = get_skills_manager()
    print(f'Current skills: {len(sm.list_skills())}')
    print('Skills list:', sm.list_skills())
except Exception as e:
    print(f'Error: {e}')
