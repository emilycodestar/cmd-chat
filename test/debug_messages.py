"""Debug helper that inspects the server message flow."""
import requests
import json
import rsa
from cryptography.fernet import Fernet

SERVER_URL = "http://127.0.0.1:1000"
ADMIN_PASSWORD = "TestPass123"

print("="*60)
print("  DEBUG - Inspecting Message Flow")
print("="*60)

# 1. Connect and retrieve the shared key
print("\n1. Requesting shared key from server...")
public_key, private_key = rsa.newkeys(2048)
pubkey_bytes = public_key.save_pkcs1()

response = requests.post(
    f"{SERVER_URL}/get_key",
    files={"pubkey": ("public.pem", pubkey_bytes)},
    data={"username": "TestUser", "password": ADMIN_PASSWORD},
    timeout=10
)

if response.status_code != 200:
    print(f"Error retrieving key: {response.status_code}")
    exit(1)

encrypted_key = response.content
symmetric_key = rsa.decrypt(encrypted_key, private_key)
fernet = Fernet(symmetric_key)
print(f"Shared key retrieved: {symmetric_key[:16].hex()}...")

# 2. Check health before sending any message
print("\n2. Health check before sending a message:")
health = requests.get(f"{SERVER_URL}/health").json()
print(f"   Messages stored: {health['messages_count']}")
print(f"   Connected users: {health['active_users']}")

# 3. Build a sample message
print("\n3. Creating sample message...")
test_message = "TestUser: This is a test message"
encrypted_msg = fernet.encrypt(test_message.encode()).decode("utf-8")
print(f"   Original: {test_message}")
print(f"   Encrypted: {encrypted_msg[:50]}...")

# 4. Local encryption test
print("\n4. Local encryption test...")
decrypted = fernet.decrypt(encrypted_msg.encode()).decode("utf-8")
if decrypted == test_message:
    print("   Encryption/decryption is working locally.")
else:
    print(f"   Error: {decrypted} != {test_message}")

print("\n" + "="*60)
print("DEBUG: If issues persist, investigate the client decryption flow")
print("       or verify the server is persisting messages correctly.")
print("="*60)

# 5. Health snapshot after the test
print("\n5. Current health snapshot:")
health = requests.get(f"{SERVER_URL}/health").json()
print(f"   Messages stored: {health['messages_count']}")
print(f"   Connected users: {health['active_users']}")

print("\nFor an end-to-end test, connect a real client, send a message,")
print("and run this script again.")
