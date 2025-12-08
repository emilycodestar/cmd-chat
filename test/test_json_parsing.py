"""Tests for JSON message parsing (replacing ast.literal_eval)."""
import json
import requests
import rsa
from cryptography.fernet import Fernet

SERVER_URL = "http://127.0.0.1:1000"
ADMIN_PASSWORD = "TestPass123"

def test_json_parsing():
    """Test that JSON parsing works correctly."""
    print("\n" + "="*60)
    print("  JSON PARSING TEST")
    print("="*60)
    
    # Generate keys
    public_key, private_key = rsa.newkeys(2048)
    pubkey_bytes = public_key.save_pkcs1()
    
    # Get symmetric key
    response = requests.post(
        f"{SERVER_URL}/get_key",
        files={"pubkey": ("public.pem", pubkey_bytes)},
        data={"username": "jsontest", "password": ADMIN_PASSWORD},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"Failed to get key: {response.status_code}")
        return False
    
    encrypted_key = response.content
    symmetric_key = rsa.decrypt(encrypted_key, private_key)
    fernet = Fernet(symmetric_key)
    
    # Test various message formats
    test_messages = [
        "jsontest: Hello world!",
        "jsontest: Message with \"quotes\"",
        "jsontest: Message with 'single quotes'",
        "jsontest: Message with {braces}",
        "jsontest: Message with [brackets]",
        "jsontest: Message with special chars: !@#$%^&*()",
    ]
    
    print("\nTesting JSON serialization/deserialization...")
    for msg in test_messages:
        try:
            # Encrypt message
            encrypted = fernet.encrypt(msg.encode()).decode("utf-8")
            
            # Create JSON payload
            payload = json.dumps({
                "text": encrypted,
                "username": "jsontest"
            })
            
            # Parse it back
            parsed = json.loads(payload)
            
            # Decrypt and verify
            decrypted = fernet.decrypt(parsed["text"].encode()).decode("utf-8")
            
            if decrypted != msg:
                print(f"   ❌ FAIL: Message mismatch for: {msg[:30]}...")
                return False
        except Exception as e:
            print(f"   ❌ FAIL: Error processing message: {e}")
            return False
    
    print("   ✅ PASS: All JSON parsing tests passed")
    return True

if __name__ == "__main__":
    test_json_parsing()
    print("\n" + "="*60)
    print("  JSON parsing tests completed!")
    print("="*60)

