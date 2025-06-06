#!/usr/bin/env python3
"""
Test runner script for the Text RPG backend.

Provides convenient commands to run different test categories:
- All tests
- Unit tests only
- Integration tests only
- Middleware tests only
- Authentication tests only
- Health check tests only
- Coverage reports
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str = None) -> int:
    """Run a command and return the exit code."""
    if description:
        print(f"\n🚀 {description}")
        print("=" * 60)

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def run_all_tests():
    """Run all tests with coverage."""
    return run_command(
        [
            "python",
            "-m",
            "pytest",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "-v",
        ],
        "Running all tests with coverage",
    )


def run_unit_tests():
    """Run only unit tests."""
    return run_command(
        ["python", "-m", "pytest", "-m", "unit", "-v"], "Running unit tests only"
    )


def run_integration_tests():
    """Run only integration tests."""
    return run_command(
        ["python", "-m", "pytest", "-m", "integration", "-v"],
        "Running integration tests only",
    )


def run_middleware_tests():
    """Run only middleware tests."""
    return run_command(
        ["python", "-m", "pytest", "-m", "middleware", "-v"],
        "Running middleware tests only",
    )


def run_auth_tests():
    """Run only authentication tests."""
    return run_command(
        ["python", "-m", "pytest", "-m", "auth", "-v"],
        "Running authentication tests only",
    )


def run_health_tests():
    """Run only health check tests."""
    return run_command(
        ["python", "-m", "pytest", "-m", "health", "-v"],
        "Running health check tests only",
    )


def run_fast_tests():
    """Run tests excluding slow ones."""
    return run_command(
        ["python", "-m", "pytest", "-m", "not slow", "-v"],
        "Running fast tests (excluding slow tests)",
    )


def run_specific_file(test_file: str):
    """Run tests in a specific file."""
    return run_command(
        ["python", "-m", "pytest", test_file, "-v"], f"Running tests in {test_file}"
    )


def run_with_coverage_report():
    """Run tests and open HTML coverage report."""
    exit_code = run_command(
        [
            "python",
            "-m",
            "pytest",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "-v",
        ],
        "Running tests with HTML coverage report",
    )

    if exit_code == 0:
        coverage_file = Path("htmlcov/index.html")
        if coverage_file.exists():
            print(f"\n📊 Coverage report generated at: {coverage_file.absolute()}")

            # Try to open the coverage report in the default browser
            try:
                import webbrowser

                webbrowser.open(f"file://{coverage_file.absolute()}")
                print("📈 Coverage report opened in browser")
            except Exception:
                print(
                    "💡 Open htmlcov/index.html in your browser to view the coverage report"
                )

    return exit_code


def check_dependencies():
    """Check if required test dependencies are installed."""
    required_packages = ["pytest", "pytest_cov", "pytest_asyncio", "httpx", "fastapi"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install with: pip install " + " ".join(missing_packages))
        return False

    return True


def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["API_RATE_LIMIT"] = "1000"

    print("✅ Test environment variables set")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for Text RPG backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run unit tests only
  python run_tests.py --integration      # Run integration tests only
  python run_tests.py --auth             # Run auth tests only
  python run_tests.py --coverage         # Run tests with HTML coverage
  python run_tests.py --fast             # Run fast tests only
  python run_tests.py --file tests/unit/test_auth_utils.py  # Run specific file
        """,
    )

    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--middleware", action="store_true", help="Run middleware tests only"
    )
    parser.add_argument(
        "--auth", action="store_true", help="Run authentication tests only"
    )
    parser.add_argument(
        "--health", action="store_true", help="Run health check tests only"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Run fast tests (exclude slow tests)"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with HTML coverage report"
    )
    parser.add_argument("--file", type=str, help="Run tests in specific file")
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if test dependencies are installed",
    )

    args = parser.parse_args()

    # Check dependencies if requested
    if args.check_deps:
        if check_dependencies():
            print("✅ All test dependencies are installed")
            return 0
        else:
            return 1

    # Set up test environment
    setup_test_environment()

    # Determine which tests to run
    exit_code = 0

    if args.unit:
        exit_code = run_unit_tests()
    elif args.integration:
        exit_code = run_integration_tests()
    elif args.middleware:
        exit_code = run_middleware_tests()
    elif args.auth:
        exit_code = run_auth_tests()
    elif args.health:
        exit_code = run_health_tests()
    elif args.fast:
        exit_code = run_fast_tests()
    elif args.coverage:
        exit_code = run_with_coverage_report()
    elif args.file:
        exit_code = run_specific_file(args.file)
    else:
        # Default: run all tests
        exit_code = run_all_tests()

    # Summary
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
