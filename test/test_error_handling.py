"""Tests for error handling and security."""
import requests

SERVER_URL = "http://127.0.0.1:1000"
ADMIN_PASSWORD = "TestPass123"

def test_error_handling():
    """Test that error messages don't leak stack traces."""
    print("\n" + "="*60)
    print("  ERROR HANDLING TEST")
    print("="*60)
    
    # Test 1: Invalid public key format
    print("\n1. Testing invalid public key format...")
    response = requests.post(
        f"{SERVER_URL}/get_key",
        files={"pubkey": ("public.pem", b"invalid key data")},
        data={"username": "test", "password": ADMIN_PASSWORD},
        timeout=5
    )
    
    if response.status_code == 400:
        error_text = response.text
        print(f"   Status: {response.status_code}")
        print(f"   Error message: {error_text}")
        
        # Check that no stack trace is exposed
        if "Traceback" in error_text or "File" in error_text or ".py" in error_text:
            print("   ❌ FAIL: Stack trace exposed!")
            return False
        else:
            print("   ✅ PASS: Clean error message")
    else:
        print(f"   Unexpected status: {response.status_code}")
        return False
    
    # Test 2: Missing public key
    print("\n2. Testing missing public key...")
    response = requests.post(
        f"{SERVER_URL}/get_key",
        data={"username": "test", "password": ADMIN_PASSWORD},
        timeout=5
    )
    
    if response.status_code == 400:
        error_text = response.text
        print(f"   Status: {response.status_code}")
        print(f"   Error message: {error_text}")
        print("   ✅ PASS: Proper error for missing key")
    else:
        print(f"   Unexpected status: {response.status_code}")
        return False
    
    # Test 3: Unauthorized access
    print("\n3. Testing unauthorized access...")
    response = requests.post(
        f"{SERVER_URL}/get_key",
        files={"pubkey": ("public.pem", b"test")},
        data={"username": "test", "password": "wrong_password"},
        timeout=5
    )
    
    if response.status_code == 401:
        print(f"   Status: {response.status_code}")
        print("   ✅ PASS: Proper unauthorized response")
    else:
        print(f"   Unexpected status: {response.status_code}")
        return False
    
    print("\n" + "="*60)
    print("  All error handling tests passed!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_error_handling()

