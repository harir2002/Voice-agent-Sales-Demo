"""
Test script to verify Twilio outbound calls work
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "https://voice-agent-sales-demo.onrender.com"

def test_outbound_call(to_number: str):
    """
    Test outbound call to verify Twilio setup
    
    Args:
        to_number: The phone number to call (e.g., +919876543210)
    """
    print("\n" + "=" * 70)
    print("📞 TESTING TWILIO OUTBOUND CALL")
    print("=" * 70)
    
    print(f"\n📋 Test Configuration:")
    print(f"   API URL: {API_BASE_URL}")
    print(f"   To Number: {to_number}")
    print(f"   Sector: banking")
    print(f"   Purpose: general")
    
    # Prepare request
    payload = {
        "to_number": to_number,
        "sector": "banking",
        "call_purpose": "general",
        "customer_name": "Test User"
    }
    
    print(f"\n🚀 Initiating call...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/twilio/call/outbound",
            json=payload,
            timeout=30
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"\n✅ SUCCESS! Call initiated!")
                print(f"   Call SID: {data.get('call_sid')}")
                print(f"   From: {data.get('from')}")
                print(f"   To: {data.get('to')}")
                print(f"   Status: {data.get('status')}")
                print(f"\n🎉 Your Twilio setup is working correctly!")
            else:
                print(f"\n❌ Call failed: {data}")
        else:
            print(f"\n❌ Error Response:")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw Response: {response.text}")
        
        print("\n" + "=" * 70)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network Error: {e}")
        print(f"   Make sure your backend is running and accessible")
        print("\n" + "=" * 70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n⚠️  Usage: python test_outbound_call.py <YOUR_PHONE_NUMBER>")
        print("   Example: python test_outbound_call.py +919876543210")
        print("\n   Replace with your actual phone number to receive the test call")
        sys.exit(1)
    
    test_number = sys.argv[1]
    
    # Validate phone number format
    if not test_number.startswith('+'):
        print("\n⚠️  Phone number should start with '+' (e.g., +919876543210)")
        test_number = input("Enter phone number with country code (e.g., +919876543210): ")
    
    test_outbound_call(test_number)
