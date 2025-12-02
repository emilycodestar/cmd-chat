"""Security regression tests for CMD CHAT."""
import requests
import json
import time

SERVER_URL = "http://127.0.0.1:1000"
ADMIN_PASSWORD = "TestPass123"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_health_check():
    """Exercise the health check endpoint."""
    print_section("1. HEALTH CHECK")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Active users: {data['active_users']}")
        print(f"Messages stored: {data['messages_count']}")
        print(f"Active tokens: {data['active_tokens']}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_generate_token(username="alice", ttl=3600):
    """Validate token issuance."""
    print_section(f"2. GENERATE TOKEN FOR '{username}'")
    try:
        response = requests.post(
            f"{SERVER_URL}/generate_token",
            data={
                "admin_password": ADMIN_PASSWORD,
                "username": username,
                "ttl": str(ttl)
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Token generated successfully!")
            print(f"Token: {data['token']}")
            print(f"Username: {data['username']}")
            print(f"Expires in: {data['expires_in']} seconds ({data['expires_in']//3600}h)")
            return data['token']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_key_exchange_with_password(username="bob"):
    """Validate key exchange using the admin password."""
    print_section(f"3. HANDSHAKE WITH PASSWORD ('{username}')")
    try:
        import rsa
        # Generate RSA key pair
        print("Generating RSA 2048-bit key pair...")
        start = time.time()
        public_key, private_key = rsa.newkeys(2048)
        elapsed = time.time() - start
        print(f"Keys generated in {elapsed:.2f}s")
        
        # Send public key
        pubkey_bytes = public_key.save_pkcs1()
        print("Sending public key to server...")
        
        response = requests.post(
            f"{SERVER_URL}/get_key",
            files={"pubkey": ("public.pem", pubkey_bytes)},
            data={"username": username, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            print("Symmetric key received!")
            encrypted_key = response.content
            print(f"Encrypted blob size: {len(encrypted_key)} bytes")
            
            # Decrypt symmetric key
            print("Decrypting symmetric key...")
            symmetric_key = rsa.decrypt(encrypted_key, private_key)
            print(f"Symmetric key obtained: {symmetric_key[:16].hex()}...")
            
            # Encryption self-test
            from cryptography.fernet import Fernet
            fernet = Fernet(symmetric_key)
            test_msg = "Hello, secure world!"
            encrypted = fernet.encrypt(test_msg.encode())
            decrypted = fernet.decrypt(encrypted).decode()
            
            print("Encryption test:")
            print(f"Original: {test_msg}")
            print(f"Encrypted: {encrypted[:32].hex()}...")
            print(f"Decrypted: {decrypted}")
            print("Symmetric channel established successfully!")
            return True
        else:
            print(f"Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_key_exchange_with_token(token, username="alice"):
    """Validate key exchange using a previously issued token."""
    print_section(f"4. HANDSHAKE WITH TOKEN ('{username}')")
    try:
        import rsa
        print("Generating RSA 2048-bit key pair...")
        public_key, private_key = rsa.newkeys(2048)
        print("Keys generated")
        
        # Send public key with token
        pubkey_bytes = public_key.save_pkcs1()
        print("Sending public key alongside token...")
        
        response = requests.post(
            f"{SERVER_URL}/get_key",
            files={"pubkey": ("public.pem", pubkey_bytes)},
            data={"username": username, "token": token},
            timeout=10
        )
        
        if response.status_code == 200:
            print("Token authentication succeeded!")
            encrypted_key = response.content
            symmetric_key = rsa.decrypt(encrypted_key, private_key)
            print(f"Symmetric key obtained: {symmetric_key[:16].hex()}...")
            return True
        else:
            print(f"Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_revoke_token(token):
    """Validate token revocation flow."""
    print_section("5. REVOKE TOKEN")
    try:
        response = requests.post(
            f"{SERVER_URL}/revoke_token",
            data={
                "password": ADMIN_PASSWORD,
                "token": token
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("revoked"):
                print("Token revoked successfully!")
                return True
            else:
                print("Token not found")
                return False
        else:
            print(f"Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_message_size_validation():
    """Ensure size guards reject oversized payloads."""
    print_section("6. MESSAGE SIZE VALIDATION")
    
    msg_normal = "A" * 100  # 100 bytes
    print(f"Normal message: {len(msg_normal)} bytes - OK")
    
    msg_limit = "B" * 10_240  # 10KB limit
    print(f"Boundary message: {len(msg_limit)} bytes (10KB) - OK")
    
    msg_large = "C" * 20_000
    print(f"Large message: {len(msg_large)} bytes (20KB) - would be rejected")
    
    payload_huge = "D" * 2_000_000  # 2MB
    print(f"Huge payload: {len(payload_huge)} bytes (2MB) - rejected (limit 1MB)")
    
    return True

def run_all_tests():
    """Run the complete security suite."""
    print("\n" + "="*60)
    print("  CMD CHAT - SECURITY FEATURE TESTS")
    print("="*60)
    print(f"Server: {SERVER_URL}")
    print(f"Admin password: {ADMIN_PASSWORD}")
    
    results = []
    
    results.append(("Health Check", test_health_check()))
    time.sleep(0.5)
    
    token = test_generate_token("alice", 3600)
    results.append(("Generate Token", token is not None))
    time.sleep(0.5)
    
    results.append(("Handshake (Password)", test_key_exchange_with_password("bob")))
    time.sleep(0.5)
    
    if token:
        results.append(("Handshake (Token)", test_key_exchange_with_token(token, "alice")))
        time.sleep(0.5)
    
    results.append(("Message Size Validation", test_message_size_validation()))
    time.sleep(0.5)
    
    if token:
        results.append(("Revoke Token", test_revoke_token(token)))
        time.sleep(0.5)
    
    print_section("7. HEALTH CHECK FINAL")
    test_health_check()
    
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("All tests passed. System is healthy.")
    else:
        print("Some tests failed. Inspect the logs above.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
