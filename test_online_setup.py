#!/usr/bin/env python3
"""
Bilka Price Monitor - Online Deployment Test
Tests that the dashboard is properly configured for online access
"""

import subprocess
import sys
import os
import time

import pytest


# This test suite requires Docker and a running dashboard; skip under pytest
# unless explicitly enabled.
if os.getenv("RUN_INTEGRATION_TESTS", "").lower() not in {"1", "true", "yes"}:
    pytest.skip("Skipping Docker/online deployment integration tests (set RUN_INTEGRATION_TESTS=1 to run)", allow_module_level=True)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

def test_dashboard_access():
    """Test if dashboard is accessible"""
    if not REQUESTS_AVAILABLE:
        print("   ⚠️  requests library not available, skipping health check")
        return True

    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        assert response.status_code == 200
    except requests.RequestException:
        pytest.fail("Dashboard health endpoint not reachable")
    except Exception:
        raise

def test_docker_compose():
    """Test if docker-compose is working"""
    try:
        result = subprocess.run(["docker-compose", "ps"],
                              capture_output=True, text=True, check=False)
        assert result.returncode == 0
    except FileNotFoundError:
        pytest.skip("docker-compose not found")
    except Exception:
        raise

def main():
    print("🔍 Bilka Price Monitor - Online Deployment Test")
    print("=" * 50)

    # Test 1: Check if Docker is running
    print("1. Checking Docker...")
    try:
        result = subprocess.run(["docker", "--version"],
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print("   ✅ Docker is installed")
        else:
            print("   ❌ Docker not found")
            return False
    except FileNotFoundError:
        print("   ❌ Docker not found in PATH")
        return False
    except Exception:
        print("   ❌ Docker not accessible")
        return False

    # Test 2: Check docker-compose
    print("2. Checking Docker Compose...")
    if test_docker_compose():
        print("   ✅ Docker Compose is working")
    else:
        print("   ❌ Docker Compose not working")
        return False

    # Test 3: Check if dashboard files exist
    print("3. Checking dashboard files...")
    required_files = [
        "docker-compose.yml",
        "Dockerfile.simple",
        "src/ui/dashboard.py",
        "main.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if not missing_files:
        print("   ✅ All required files present")
    else:
        print(f"   ❌ Missing files: {', '.join(missing_files)}")
        return False

    # Test 4: Try to start dashboard
    print("4. Testing dashboard startup...")
    print("   Starting dashboard (this may take a moment)...")

    process = None
    try:
        # Start in background
        process = subprocess.Popen(["docker-compose", "up", "--build"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        # Wait for startup
        print("   Waiting for dashboard to start...")
        startup_success = False
        for _ in range(30):  # Wait up to 30 seconds
            if test_dashboard_access():
                print("   ✅ Dashboard is accessible at http://localhost:8501")
                startup_success = True
                break
            time.sleep(1)

        if not startup_success:
            print("   ❌ Dashboard failed to start within 30 seconds")
            return False

    except KeyboardInterrupt:
        print("   Test interrupted by user")
        return False
    except Exception as e:
        print(f"   ❌ Error starting dashboard: {e}")
        return False
    finally:
        # Cleanup
        if process:
            try:
                process.terminate()
                process.wait(timeout=10)
            except:
                pass

        try:
            subprocess.run(["docker-compose", "down"],
                         capture_output=True, check=False)
        except:
            pass

    print("\n🎉 All tests passed!")
    print("\n🚀 Your dashboard is ready for online deployment!")
    print("\nNext steps:")
    print("1. Run: docker-compose up --build")
    print("2. Run: ngrok http 8501")
    print("3. Share the ngrok HTTPS URL with anyone!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)