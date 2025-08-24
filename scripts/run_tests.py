
"""
Test runner script for StegoCrypt Suite.
Run tests with various options and generate reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="StegoCrypt Suite Test Runner")
    parser.add_argument("--type", choices=["all", "crypto", "stego", "unit", "integration"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    print("🚀 StegoCrypt Suite Test Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("Backend").exists():
        print("❌ Error: Backend directory not found. Run this script from the project root.")
        sys.exit(1)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.coverage:
        cmd.extend(["--cov=Backend", "--cov-report=term-missing"])
    
    if args.html:
        cmd.extend(["--cov=Backend", "--cov-report=html"])
    
    # Add test type filters
    if args.type == "crypto":
        cmd.extend(["-m", "cryptography"])
    elif args.type == "stego":
        cmd.extend(["-m", "steganography"])
    elif args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    
    # Run tests
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n🎉 All tests completed successfully!")
        
        if args.coverage or args.html:
            print("\n📊 Coverage report generated!")
            if args.html:
                print("📁 HTML report: htmlcov/index.html")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()


