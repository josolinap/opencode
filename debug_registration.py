#!/usr/bin/env python3
"""
Debug script to test skills registration process
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'neo-clone'))

def test_imports():
    """Test if all skill modules can be imported"""
    print("=== Testing Skill Module Imports ===")
    
    try:
        # Test additional_skills import
        try:
            from additional_skills import PlanningSkill, WebSearchSkill, MLTrainingSkill
            print("+ additional_skills imported successfully")
            print(f"  - PlanningSkill: {PlanningSkill}")
            print(f"  - WebSearchSkill: {WebSearchSkill}")
            print(f"  - MLTrainingSkill: {MLTrainingSkill}")
        except ImportError as e:
            print(f"- additional_skills import failed: {e}")
            
        # Test more_skills import
        try:
            from more_skills import FileManagerSkill, TextAnalysisSkill
            print("+ more_skills imported successfully")
            print(f"  - FileManagerSkill: {FileManagerSkill}")
            print(f"  - TextAnalysisSkill: {TextAnalysisSkill}")
        except ImportError as e:
            print(f"- more_skills import failed: {e}")
            
        # Test data_inspector import
        try:
            from data_inspector import DataInspectorSkill
            print("+ data_inspector imported successfully")
            print(f"  - DataInspectorSkill: {DataInspectorSkill}")
        except ImportError as e:
            print(f"- data_inspector import failed: {e}")
            
    except Exception as e:
        print(f"- Import test failed: {e}")

def test_skills_registration():
    """Test skills manager registration"""
    print("\n=== Testing Skills Manager Registration ===")
    
    try:
        from skills import get_skills_manager
        
        # Get skills manager
        manager = get_skills_manager()
        print(f"Skills manager created: {manager}")
        
        # List all registered skills
        skills = manager.list_skills()
        print(f"Total registered skills: {len(skills)}")
        print("Skills:")
        for skill in skills:
            print(f"  - {skill}")
            
        # Get skill statistics
        stats = manager.get_statistics()
        print(f"\nSkill Statistics:")
        print(f"  Total skills: {stats['total_skills']}")
        print(f"  Category breakdown: {list(stats['category_statistics'].keys())}")
        
        # Test individual skill info
        for skill_name in skills:
            info = manager.get_skill_info(skill_name)
            if info:
                print(f"\n{skill_name}:")
                print(f"  Category: {info['category']}")
                print(f"  Description: {info['description']}")
                print(f"  Status: {info['status']}")
                print(f"  Available: {info['is_available']}")
                
    except Exception as e:
        print(f"- Skills registration test failed: {e}")
        import traceback
        traceback.print_exc()

def test_builtin_skills():
    """Test builtin skills availability"""
    print("\n=== Testing Built-in Skills ===")
    
    try:
        from skills import (
            CodeGenerationSkill, DataAnalysisSkill, ConversationSkill,
            DebuggingSkill, OptimizationSkill, AdvancedReasoningSkill
        )
        
        builtin_skills = [
            ("CodeGenerationSkill", CodeGenerationSkill),
            ("DataAnalysisSkill", DataAnalysisSkill),
            ("ConversationSkill", ConversationSkill),
            ("DebuggingSkill", DebuggingSkill),
            ("OptimizationSkill", OptimizationSkill),
            ("AdvancedReasoningSkill", AdvancedReasoningSkill)
        ]
        
        for name, skill_class in builtin_skills:
            try:
                skill_instance = skill_class()
                print(f"+ {name}: {skill_instance.metadata.name}")
            except Exception as e:
                print(f"- {name} failed: {e}")
                
    except Exception as e:
        print(f"- Built-in skills test failed: {e}")

if __name__ == "__main__":
    test_imports()
    test_builtin_skills()
    test_skills_registration()