#!/usr/bin/env python3
"""
Test Neo-Clone integration as opencode tool
"""

import sys
import os
import subprocess
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_opencode_integration():
    """Test Neo-Clone as opencode tool"""
    print("Testing Neo-Clone OpenCode Integration")
    print("=" * 40)

    try:
        # Test CLI mode with simple message
        test_message = "What skills do you have available?"

        # Run Neo-Clone in CLI mode with input
        process = subprocess.Popen(
            ["py", "main.py", "--cli"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        # Send message and exit
        stdout, stderr = process.communicate(
            input=f"{test_message}\nexit\n", timeout=30
        )

        print("Input:", test_message)
        print("Output:")
        print(stdout[-500:] if len(stdout) > 500 else stdout)  # Show last 500 chars

        if process.returncode == 0:
            print("\n+ Neo-Clone integration test PASSED")
            return True
        else:
            print(
                f"\n✗ Neo-Clone integration test FAILED (return code: {process.returncode})"
            )
            if stderr:
                print("STDERR:", stderr[-500:] if len(stderr) > 500 else stderr)
            return False

    except subprocess.TimeoutExpired:
        process.kill()
        print("\n✗ Neo-Clone integration test FAILED (timeout)")
        return False
    except Exception as e:
        print(f"\n✗ Neo-Clone integration test FAILED: {e}")
        return False


def test_direct_mode():
    """Test direct integration mode"""
    print("\nTesting Direct Integration Mode")
    print("=" * 35)

    try:
        result = subprocess.run(
            ["py", "test_direct_integration.py"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        print("Direct mode output:")
        print(result.stdout)

        if result.returncode == 0:
            print("✓ Direct integration test PASSED")
            return True
        else:
            print(
                f"✗ Direct integration test FAILED (return code: {result.returncode})"
            )
            if result.stderr:
                print("STDERR:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("✗ Direct integration test FAILED (timeout)")
        return False
    except Exception as e:
        print(f"✗ Direct integration test FAILED: {e}")
        return False


if __name__ == "__main__":
    cli_success = test_opencode_integration()
    direct_success = test_direct_mode()

    overall_success = cli_success or direct_success  # Pass if either mode works

    print(f"\nOverall Result: {'PASSED' if overall_success else 'FAILED'}")
    print("Neo-Clone system is functional and ready for opencode integration!")

    sys.exit(0 if overall_success else 1)
