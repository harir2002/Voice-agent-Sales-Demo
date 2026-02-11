"""
Quick Twilio Phone Number Verification Script
This script helps you verify which phone number is configured and where
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_twilio_config():
    """Check Twilio configuration"""
    print("\n" + "=" * 70)
    print("🔍 TWILIO CONFIGURATION CHECK")
    print("=" * 70)
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    print(f"\n📋 Current Configuration (.env file):")
    print(f"   Account SID: {account_sid[:10]}...{account_sid[-4:] if account_sid else 'NOT SET'}")
    print(f"   Auth Token:  {'*' * 20}{auth_token[-4:] if auth_token else 'NOT SET'}")
    print(f"   Phone Number: {phone_number or 'NOT SET'}")
    
    # Validate phone number format
    if phone_number:
        if not phone_number.startswith('+'):
            print(f"\n⚠️  WARNING: Phone number should start with '+' (e.g., +19062928716)")
        else:
            print(f"\n✅ Phone number format looks correct")
    else:
        print(f"\n❌ Phone number is NOT SET")
    
    # Try to verify with Twilio API
    try:
        from twilio.rest import Client
        
        if account_sid and auth_token:
            print(f"\n📞 Connecting to Twilio to verify...")
            client = Client(account_sid, auth_token)
            
            # Fetch account info
            account = client.api.accounts(account_sid).fetch()
            print(f"✅ Twilio Account Status: {account.status}")
            print(f"✅ Account Name: {account.friendly_name}")
            
            # Fetch purchased phone numbers
            print(f"\n📱 Your Purchased Twilio Phone Numbers:")
            incoming_numbers = client.incoming_phone_numbers.list(limit=20)
            
            if not incoming_numbers:
                print(f"   ❌ No phone numbers found in your account!")
                print(f"   → Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/buy")
                print(f"   → Purchase a phone number first")
            else:
                for idx, number in enumerate(incoming_numbers, 1):
                    print(f"   {idx}. {number.phone_number} - {number.friendly_name}")
                    
                    # Check if this matches the configured number
                    if number.phone_number == phone_number:
                        print(f"      ✅ This matches your configured number!")
                
                # Check if configured number is in the list
                purchased_numbers = [n.phone_number for n in incoming_numbers]
                if phone_number and phone_number not in purchased_numbers:
                    print(f"\n⚠️  WARNING: Your configured number '{phone_number}' is NOT in your purchased numbers!")
                    print(f"   You can only make calls from purchased numbers.")
                    print(f"   Please update TWILIO_PHONE_NUMBER in .env to one of the above numbers.")
        
        print("\n" + "=" * 70)
        print("✅ Configuration check complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error connecting to Twilio: {e}")
        print(f"   Please verify your Account SID and Auth Token are correct")
        print(f"   Get them from: https://console.twilio.com/")

if __name__ == "__main__":
    check_twilio_config()
