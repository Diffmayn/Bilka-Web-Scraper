#!/usr/bin/env python3
"""
Bilka Price Monitor - Configuration Verification
Verifies that all files are properly configured for online deployment
"""

import os

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"   ✅ {description}: {file_path}")
        return True
    else:
        print(f"   ❌ Missing {description}: {file_path}")
        return False

def check_docker_compose_config():
    """Check docker-compose.yml configuration"""
    if not YAML_AVAILABLE:
        print("   ⚠️  PyYAML not available, skipping detailed config check")
        return check_file_exists('docker-compose.yml', 'Docker Compose file exists')

    try:
        with open('docker-compose.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Check for required settings
        service = config.get('services', {}).get('bilka-monitor', {})

        # Check environment variables
        env_vars = service.get('environment', [])
        required_env = [
            'STREAMLIT_SERVER_HEADLESS=true',
            'STREAMLIT_SERVER_ADDRESS=0.0.0.0',
            'STREAMLIT_SERVER_PORT=8501'
        ]

        missing_env = []
        for req_env in required_env:
            if req_env not in env_vars:
                missing_env.append(req_env)

        if not missing_env:
            print("   ✅ Docker Compose environment variables configured")
            return True
        else:
            print(f"   ❌ Missing environment variables: {missing_env}")
            return False

    except FileNotFoundError:
        print("   ❌ docker-compose.yml not found")
        return False
    except yaml.YAMLError as e:
        print(f"   ❌ Error parsing docker-compose.yml: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error reading docker-compose.yml: {e}")
        return False

def check_dockerfile_config():
    """Check Dockerfile.simple configuration"""
    try:
        with open('Dockerfile.simple', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required configurations
        checks = [
            ('STREAMLIT_SERVER_HEADLESS=true', 'Streamlit headless mode'),
            ('STREAMLIT_SERVER_ADDRESS=0.0.0.0', 'Streamlit address binding'),
            ('EXPOSE 8501', 'Port exposure'),
            ('HEALTHCHECK', 'Health check configuration')
        ]

        all_passed = True
        for check_text, description in checks:
            if check_text in content:
                print(f"   ✅ {description} configured")
            else:
                print(f"   ❌ {description} missing")
                all_passed = False

        return all_passed

    except FileNotFoundError:
        print("   ❌ Dockerfile.simple not found")
        return False
    except Exception as e:
        print(f"   ❌ Error reading Dockerfile.simple: {e}")
        return False

def check_dashboard_file():
    """Check if dashboard file exists and is readable"""
    try:
        with open('src/ui/dashboard.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for basic Streamlit imports
        if 'import streamlit as st' in content:
            print("   ✅ Dashboard file has Streamlit imports")
            return True
        else:
            print("   ❌ Dashboard file missing Streamlit imports")
            return False

    except FileNotFoundError:
        print("   ❌ Dashboard file not found")
        return False
    except Exception as e:
        print(f"   ❌ Error reading dashboard file: {e}")
        return False

def main():
    print("🔍 Bilka Price Monitor - Configuration Verification")
    print("=" * 55)
    print("Checking if your project is ready for online deployment...\n")

    all_checks_passed = True

    # Check 1: Required files
    print("1. Checking required files...")
    required_files = [
        ('docker-compose.yml', 'Docker Compose configuration'),
        ('Dockerfile.simple', 'Docker container definition'),
        ('src/ui/dashboard.py', 'Streamlit dashboard'),
        ('main.py', 'Main application entry point'),
        ('requirements.txt', 'Python dependencies')
    ]

    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print()

    # Check 2: Docker Compose configuration
    print("2. Checking Docker Compose configuration...")
    if not check_docker_compose_config():
        all_checks_passed = False
    print()

    # Check 3: Dockerfile configuration
    print("3. Checking Dockerfile configuration...")
    if not check_dockerfile_config():
        all_checks_passed = False
    print()

    # Check 4: Dashboard file
    print("4. Checking dashboard implementation...")
    if not check_dashboard_file():
        all_checks_passed = False
    print()

    # Summary
    print("=" * 55)
    if all_checks_passed:
        print("🎉 Configuration verification PASSED!")
        print("\n🚀 Your dashboard is ready for online deployment!")
        print("\n📋 Next steps:")
        print("1. Start the dashboard: docker-compose up --build")
        print("2. Create online tunnel: ngrok http 8501")
        print("3. Share the HTTPS URL from ngrok!")
        print("\n📖 For detailed instructions, see: ONLINE_DEPLOYMENT_GUIDE.md")
        return True
    else:
        print("❌ Configuration verification FAILED!")
        print("\n🔧 Please check the issues above and fix them.")
        print("📖 See ONLINE_DEPLOYMENT_GUIDE.md for help.")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)