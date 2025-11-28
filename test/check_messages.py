"""Utility script to inspect server state during local testing."""
import requests
import time

SERVER_URL = "http://127.0.0.1:1000"

print("Checking server health...")
try:
    response = requests.get(f"{SERVER_URL}/health", timeout=5)
    data = response.json()
    print(f"Status: {data['status']}")
    print(f"Connected users: {data['active_users']}")
    print(f"Messages stored: {data['messages_count']}")
    print(f"Active tokens: {data['active_tokens']}")
    
    if data['messages_count'] > 0:
        print(f"\nServer currently stores {data['messages_count']} messages.")
        print("Messages are being persisted correctly in memory.")
    else:
        print("\nServer does not have messages yet.")
        print("Send a few messages and run this script again.")
        
except Exception as e:
    print(f"Error connecting to server: {e}")
    print("Ensure the CMD CHAT server is running.")
