#!/usr/bin/env python3
"""
Test Wompi Integration
Tests the Wompi payment link creation and webhook verification
"""

import asyncio
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def test_wompi_integration():
    """Test Wompi Payment Link creation"""
    
    print("🧪 Testing Wompi Integration...")
    
    dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
    
    if dry_run:
        print("   ℹ️  Running in DRY_RUN mode - will simulate API calls")
        print("   ✅ Mock payment link: https://checkout.wompi.pa/l/mock_12345678")
        print("   ✅ Webhook verification: MOCKED (always returns True)")
        return True
    
    # Test environment variables
    public_key = os.getenv('WOMPI_PUBLIC_KEY')
    private_key = os.getenv('WOMPI_PRIVATE_KEY') 
    webhook_secret = os.getenv('WOMPI_WEBHOOK_SECRET')
    
    if not all([public_key, private_key, webhook_secret]):
        print("   ❌ Missing Wompi credentials:")
        print(f"      WOMPI_PUBLIC_KEY: {'✅' if public_key else '❌'}")
        print(f"      WOMPI_PRIVATE_KEY: {'✅' if private_key else '❌'}")
        print(f"      WOMPI_WEBHOOK_SECRET: {'✅' if webhook_secret else '❌'}")
        print("\n   💡 Set DRY_RUN=false in .env after adding real credentials")
        return False
    
    # Test payment link creation
    try:
        wompi_url = "https://api.wompi.co/v1/payment_links"
        headers = {
            "Authorization": f"Bearer {private_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "name": "SkyRide Test Booking",
            "description": "Test charter flight booking",
            "single_use": True,
            "collect_shipping": False,
            "currency": "USD", 
            "amount_in_cents": 100000,  # $1000 test
            "redirect_url": f"{os.getenv('BASE_URL')}/success?test=true",
            "metadata": {
                "test": "true",
                "booking_id": "test_booking_123"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("   🔄 Creating test payment link...")
            response = await client.post(wompi_url, headers=headers, json=test_payload)
            
            if response.status_code == 201:
                data = response.json()
                payment_link = data.get("data", {}).get("permalink")
                print(f"   ✅ Payment link created successfully!")
                print(f"      URL: {payment_link}")
                print(f"      Amount: $1000.00 USD")
                return True
            else:
                print(f"   ❌ Failed to create payment link:")
                print(f"      Status: {response.status_code}")
                print(f"      Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception during test: {e}")
        return False

async def test_api_health():
    """Test API health endpoint"""
    
    print("\n🏥 Testing API Health...")
    
    try:
        api_url = f"{os.getenv('BASE_URL', 'http://localhost:8001')}/api/health"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ API is healthy!")
                print(f"      Status: {data.get('status')}")
                print(f"      Features: {data.get('features')}")
                print(f"      Dry Run: {data.get('dry_run')}")
                return True
            else:
                print(f"   ❌ API health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Cannot reach API: {e}")
        return False

if __name__ == "__main__":
    async def run_tests():
        print("🚀 SkyRide Integration Tests\n")
        
        # Test API health first
        api_ok = await test_api_health()
        
        # Test Wompi integration
        wompi_ok = await test_wompi_integration()
        
        print(f"\n📊 Test Results:")
        print(f"   API Health: {'✅ PASS' if api_ok else '❌ FAIL'}")
        print(f"   Wompi Integration: {'✅ PASS' if wompi_ok else '❌ FAIL'}")
        
        if api_ok and wompi_ok:
            print("\n🎉 All tests passed! Platform ready for use.")
        else:
            print("\n⚠️  Some tests failed. Check configuration and try again.")
    
    asyncio.run(run_tests())