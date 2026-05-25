#!/usr/bin/env python3
"""Script to create a test user for development"""

import sys
sys.path.insert(0, '/app')

from app.infrastructure.user_repository import UserRepository
from app.application.auth_service import AuthService

def main():
    try:
        user_repo = UserRepository()
        
        # Create test user
        test_email = "test@example.com"
        test_password = "Test123!@"  # Max 72 bytes for bcrypt
        
        user = user_repo.create_user(
            email=test_email,
            password=test_password,
            full_name="Test User"
        )
        
        print(f"✅ Test user created successfully!")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   Full name: Test User")
        
    except ValueError as e:
        if "already exists" in str(e):
            print(f"⚠️  Test user already exists: {str(e)}")
            return 0
        else:
            print(f"❌ Error: {str(e)}")
            return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
