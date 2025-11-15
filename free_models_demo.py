#!/usr/bin/env python3
"""
Free Models Integration Demo
Shows how to use the free model scanner and integration system
"""

import subprocess
import json
import os
import sys

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def demo_free_models():
    """Demonstrate the free models integration system"""
    
    print("[FREE MODELS] OpenCode Free Models Integration Demo")
    print("=" * 50)
    
    # 1. Show available free models using OpenCode CLI
    print("\n1. Available Free Models (via OpenCode CLI):")
    print("-" * 40)
    
    success, output, error = run_command(
        'bun run ./src/index.ts models free --limit 10',
        cwd='packages/opencode'
    )
    
    if success:
        print(output)
    else:
        print(f"Error: {error}")
    
    # 2. Use free model scanner for detailed analysis
    print("\n2. Detailed Analysis (via Free Model Scanner):")
    print("-" * 50)
    
    success, output, error = run_command(
        'py free_model_scanner.py scan',
        cwd='neo-clone'
    )
    
    if success:
        print(output)
    else:
        print(f"Error: {error}")
    
    # 3. Get model recommendations for a specific task
    print("\n3. Model Recommendations for ML Task:")
    print("-" * 45)
    
    success, output, error = run_command(
        'bun run ./src/index.ts models recommend --task "Create a Python machine learning script" --limit 3',
        cwd='packages/opencode'
    )
    
    if success:
        print(output)
    else:
        print(f"Error: {error}")
    
    # 4. Generate integration code for best free model
    print("\n4. Integration Code for Big Pickle:")
    print("-" * 35)
    
    success, output, error = run_command(
        'py free_model_scanner.py generate opencode/big-pickle',
        cwd='neo-clone'
    )
    
    if success:
        print(output)
    else:
        print(f"Error: {error}")
    
    # 5. Show model capabilities comparison
    print("\n5. Free Model Capabilities Comparison:")
    print("-" * 42)
    
    success, output, error = run_command(
        'bun run ./src/index.ts models list --cost free --format json',
        cwd='packages/opencode'
    )
    
    if success:
        try:
            models = json.loads(output)
            print(f"{'Model':<25} {'Reasoning':<10} {'Tool Call':<10} {'Attachment':<11} {'Context':<10}")
            print("-" * 70)
            
            for model in models:
                name = f"{model['provider']}/{model['model']}"
                reasoning = "Yes" if model['capabilities']['reasoning'] else "No"
                tool_call = "Yes" if model['capabilities']['tool_call'] else "No"
                attachment = "Yes" if model['capabilities']['attachment'] else "No"
                context = str(model['limits']['context'])[:8]
                
                print(f"{name:<25} {reasoning:<10} {tool_call:<10} {attachment:<11} {context:<10}")
        except json.JSONDecodeError:
            print("Failed to parse model data")
    else:
        print(f"Error: {error}")
    
    print("\n[SUCCESS] Demo Complete!")
    print("\nKey Features:")
    print("• Automatic free model discovery")
    print("• Integration scoring and recommendations")
    print("• Code generation for seamless integration")
    print("• Real-time monitoring for new models")
    print("• CLI and Neo-Clone brain integration")

if __name__ == "__main__":
    demo_free_models()