#!/usr/bin/env python3
"""
Comprehensive Health Check Test Runner

This script demonstrates the implementation of the HEALTH CHECKS ENHANCEMENT.md
by running both mocked and real AI service tests to show the difference.

Usage:
    python run_health_check_tests.py --help
    python run_health_check_tests.py --mocked-only    # Fast tests (0.00s)
    python run_health_check_tests.py --real-only      # Slow tests (2-5s each)
    python run_health_check_tests.py --all           # Both mocked and real
    python run_health_check_tests.py --health-check  # Run comprehensive health check
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        duration = time.time() - start_time
        
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Return code: {result.returncode}")
        
        if result.stdout:
            print(f"📤 stdout: {result.stdout[:200]}...")
        if result.stderr:
            print(f"📤 stderr: {result.stderr[:200]}...")
            
        return result.returncode == 0, duration
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out after 5 minutes")
        return False, time.time() - start_time
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False, time.time() - start_time

def run_mocked_tests():
    """Run mocked AI service tests (should be fast)"""
    print("\n" + "="*60)
    print("🧪 RUNNING MOCKED AI SERVICE TESTS")
    print("="*60)
    print("These tests should run in 0.00s because they don't call real AI services")
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/integration/test_real_vs_mocked_ai.py::TestMockedAIServices",
        "-v", "--tb=short"
    ]
    
    success, duration = run_command(cmd, "Mocked AI Service Tests")
    
    if success:
        print("✅ Mocked tests completed successfully")
        if duration < 1.0:
            print("⚡ Tests were fast (mocked) - as expected")
        else:
            print("⚠️ Tests were slower than expected - might be calling real services")
    else:
        print("❌ Mocked tests failed")
    
    return success, duration

def run_real_tests():
    """Run real AI service tests (should be slow)"""
    print("\n" + "="*60)
    print("🤖 RUNNING REAL AI SERVICE TESTS")
    print("="*60)
    print("These tests should take 2-5 seconds each because they call real AI services")
    
    # Check if API keys are available
    gemini_key = os.getenv('GEMINI_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not gemini_key and not openai_key:
        print("⚠️ No AI API keys found (GEMINI_API_KEY or OPENAI_API_KEY)")
        print("Skipping real AI tests - they would fail without API keys")
        return True, 0.0
    
    print(f"🔑 Gemini API Key: {'Set' if gemini_key else 'Not set'}")
    print(f"🔑 OpenAI API Key: {'Set' if openai_key else 'Not set'}")
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/integration/test_real_vs_mocked_ai.py::TestRealAIServices",
        "-v", "--tb=short", "-s"  # -s to show print statements
    ]
    
    success, duration = run_command(cmd, "Real AI Service Tests")
    
    if success:
        print("✅ Real AI tests completed successfully")
        if duration > 5.0:
            print("🐌 Tests were slow (real AI calls) - as expected")
        else:
            print("⚠️ Tests were faster than expected - might be mocked")
    else:
        print("❌ Real AI tests failed")
    
    return success, duration

def run_comprehensive_health_check():
    """Run comprehensive health check"""
    print("\n" + "="*60)
    print("🏥 RUNNING COMPREHENSIVE HEALTH CHECK")
    print("="*60)
    print("This will test all health check categories from HEALTH CHECKS ENHANCEMENT.md")
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/integration/test_comprehensive_health_checks.py",
        "-v", "--tb=short"
    ]
    
    success, duration = run_command(cmd, "Comprehensive Health Check Tests")
    
    if success:
        print("✅ Comprehensive health check completed successfully")
    else:
        print("❌ Comprehensive health check failed")
    
    return success, duration

def run_ai_comparison_tests():
    """Run AI service comparison tests"""
    print("\n" + "="*60)
    print("📊 RUNNING AI SERVICE COMPARISON TESTS")
    print("="*60)
    print("This will demonstrate the performance difference between mocked and real tests")
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/integration/test_real_vs_mocked_ai.py::TestAIServiceComparison",
        "-v", "--tb=short", "-s"
    ]
    
    success, duration = run_command(cmd, "AI Service Comparison Tests")
    
    if success:
        print("✅ AI comparison tests completed successfully")
    else:
        print("❌ AI comparison tests failed")
    
    return success, duration

def main():
    parser = argparse.ArgumentParser(description='Run health check tests')
    parser.add_argument('--mocked-only', action='store_true', 
                       help='Run only mocked tests (fast)')
    parser.add_argument('--real-only', action='store_true', 
                       help='Run only real AI tests (slow)')
    parser.add_argument('--all', action='store_true', 
                       help='Run both mocked and real tests')
    parser.add_argument('--health-check', action='store_true', 
                       help='Run comprehensive health check')
    parser.add_argument('--comparison', action='store_true', 
                       help='Run AI service comparison tests')
    
    args = parser.parse_args()
    
    if not any([args.mocked_only, args.real_only, args.all, args.health_check, args.comparison]):
        parser.print_help()
        return
    
    print("🚀 HEALTH CHECK TEST RUNNER")
    print("="*60)
    print("This demonstrates the implementation of HEALTH CHECKS ENHANCEMENT.md")
    print("")
    
    total_start = time.time()
    results = []
    
    try:
        if args.mocked_only or args.all:
            success, duration = run_mocked_tests()
            results.append(("Mocked Tests", success, duration))
        
        if args.real_only or args.all:
            success, duration = run_real_tests()
            results.append(("Real AI Tests", success, duration))
        
        if args.health_check:
            success, duration = run_comprehensive_health_check()
            results.append(("Health Check", success, duration))
        
        if args.comparison:
            success, duration = run_ai_comparison_tests()
            results.append(("AI Comparison", success, duration))
        
        # Summary
        total_duration = time.time() - total_start
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for name, success, duration in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{name:20} {status:10} {duration:6.2f}s")
        
        print(f"{'Total':20} {'':10} {total_duration:6.2f}s")
        
        all_passed = all(success for _, success, _ in results)
        if all_passed:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️ Some tests failed - check the output above")
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

