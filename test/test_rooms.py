"""Tests for room functionality."""
import requests
import json
import rsa
from cryptography.fernet import Fernet

SERVER_URL = "http://127.0.0.1:1000"
ADMIN_PASSWORD = "TestPass123"

def test_room_key_generation():
    """Test that different rooms get different keys."""
    print("\n" + "="*60)
    print("  ROOM KEY GENERATION TEST")
    print("="*60)
    
    # Generate keys for room1
    public_key1, private_key1 = rsa.newkeys(2048)
    pubkey_bytes1 = public_key1.save_pkcs1()
    
    response1 = requests.post(
        f"{SERVER_URL}/get_key",
        files={"pubkey": ("public.pem", pubkey_bytes1)},
        data={"username": "user1", "password": ADMIN_PASSWORD, "room_id": "room1"},
        timeout=10
    )
    
    if response1.status_code != 200:
        print(f"Failed to get key for room1: {response1.status_code}")
        return False
    
    encrypted_key1 = response1.content
    symmetric_key1 = rsa.decrypt(encrypted_key1, private_key1)
    
    # Generate keys for room2
    public_key2, private_key2 = rsa.newkeys(2048)
    pubkey_bytes2 = public_key2.save_pkcs1()
    
    response2 = requests.post(
        f"{SERVER_URL}/get_key",
        files={"pubkey": ("public.pem", pubkey_bytes2)},
        data={"username": "user2", "password": ADMIN_PASSWORD, "room_id": "room2"},
        timeout=10
    )
    
    if response2.status_code != 200:
        print(f"Failed to get key for room2: {response2.status_code}")
        return False
    
    encrypted_key2 = response2.content
    symmetric_key2 = rsa.decrypt(encrypted_key2, private_key2)
    
    # Keys should be different (per-client keys)
    if symmetric_key1 == symmetric_key2:
        print("❌ FAIL: Keys are identical (should be per-client)")
        return False
    
    print("✅ PASS: Per-client keys generated correctly")
    return True

if __name__ == "__main__":
    test_room_key_generation()

