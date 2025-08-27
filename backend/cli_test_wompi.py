#!/usr/bin/env python3
"""
SkyRide Wompi Integration CLI Test Tool
Comprehensive testing utility for Wompi payment integration
"""

import asyncio
import click
import httpx
import json
from datetime import datetime
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SkyRideWompiTester:
    def __init__(self):
        self.base_url = "https://charter-hub-1.preview.emergentagent.com/api"
        self.wompi_public_key = os.getenv('WOMPI_PUBLIC_KEY', '__PROVIDED__')
        self.wompi_private_key = os.getenv('WOMPI_PRIVATE_KEY', '__PROVIDED__')
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        
    async def test_api_health(self):
        """Test API health endpoint"""
        click.echo("🏥 Testing API Health...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    click.echo("   ✅ API is healthy!")
                    click.echo(f"      Status: {data.get('status')}")
                    click.echo(f"      DRY_RUN: {data.get('dry_run')}")
                    click.echo(f"      Features: {data.get('features')}")
                    return True
                else:
                    click.echo(f"   ❌ API health check failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            click.echo(f"   ❌ Cannot reach API: {e}")
            return False
    
    async def test_listings(self):
        """Test listings endpoint"""
        click.echo("📋 Testing Listings Endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/listings")
                
                if response.status_code == 200:
                    listings = response.json()
                    click.echo(f"   ✅ Retrieved {len(listings)} listings")
                    
                    for i, listing in enumerate(listings[:3]):  # Show first 3
                        operator = listing.get('operator', {})
                        aircraft = listing.get('aircraft', {})
                        route = listing.get('route', {})
                        
                        click.echo(f"      {i+1}. {aircraft.get('model', 'Unknown')} - "
                                 f"{route.get('origin', 'Unknown')} → {route.get('destination', 'Unknown')}")
                        click.echo(f"         Price: ${listing.get('totalPrice', 0):,}")
                        click.echo(f"         Operator: {operator.get('name', 'Unknown')}")
                    
                    return listings[0]['_id'] if listings else None
                else:
                    click.echo(f"   ❌ Listings test failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            click.echo(f"   ❌ Listings test error: {e}")
            return None
    
    async def test_quote_creation(self, listing_id: str):
        """Test quote creation"""
        click.echo("💬 Testing Quote Creation...")
        
        quote_data = {
            "listingId": listing_id,
            "passengers": 2,
            "departureDate": "2024-01-15",
            "email": "test@skyride.city",
            "phone": "+507 6000-0000"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/quotes",
                    json=quote_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    quote = response.json()
                    click.echo(f"   ✅ Quote created successfully!")
                    click.echo(f"      Token: {quote.get('token')}")
                    click.echo(f"      Total Price: ${quote.get('totalPrice', 0):,}")
                    click.echo(f"      Expires At: {quote.get('expiresAt')}")
                    click.echo(f"      Hosted URL: {quote.get('hostedQuoteUrl')}")
                    return quote.get('token')
                else:
                    click.echo(f"   ❌ Quote creation failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        click.echo(f"      Error: {error_data}")
                    except:
                        click.echo(f"      Response: {response.text}")
                    return None
                    
        except Exception as e:
            click.echo(f"   ❌ Quote creation error: {e}")
            return None
    
    async def test_quote_retrieval(self, token: str):
        """Test quote retrieval by token"""
        click.echo("🔍 Testing Quote Retrieval...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/quotes/{token}")
                
                if response.status_code == 200:
                    quote = response.json()
                    click.echo(f"   ✅ Quote retrieved successfully!")
                    click.echo(f"      Status: {quote.get('status')}")
                    click.echo(f"      Base Price: ${quote.get('basePrice', 0):,}")
                    click.echo(f"      Service Fee: ${quote.get('serviceFee', 0):,}")
                    click.echo(f"      Aircraft: {quote.get('aircraft', {}).get('model')}")
                    return True
                else:
                    click.echo(f"   ❌ Quote retrieval failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            click.echo(f"   ❌ Quote retrieval error: {e}")
            return False
    
    async def test_hold_creation(self, token: str):
        """Test hold creation"""
        click.echo("⏰ Testing Hold Creation...")
        
        hold_data = {
            "token": token,
            "depositAmount": 500.00
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/holds",
                    json=hold_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    hold = response.json()
                    click.echo(f"   ✅ Hold created successfully!")
                    click.echo(f"      Hold ID: {hold.get('holdId')}")
                    click.echo(f"      Expires At: {hold.get('expiresAt')}")
                    return hold.get('holdId')
                else:
                    click.echo(f"   ❌ Hold creation failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        click.echo(f"      Error: {error_data}")
                    except:
                        click.echo(f"      Response: {response.text}")
                    return None
                    
        except Exception as e:
            click.echo(f"   ❌ Hold creation error: {e}")
            return None
    
    async def test_new_features(self):
        """Test new features: availability, WordPress, analytics"""
        click.echo("🆕 Testing New Features...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test availability endpoint
                response = await client.get(f"{self.base_url}/availability")
                if response.status_code == 200:
                    availability = response.json()
                    click.echo(f"   ✅ Availability system: {availability.get('system')}")
                else:
                    click.echo(f"   ❌ Availability test failed: {response.status_code}")
                
                # Test WordPress hot deals
                response = await client.get(f"{self.base_url}/wordpress/hot-deals")
                if response.status_code == 200:
                    deals = response.json()
                    click.echo(f"   ✅ WordPress hot deals: {deals.get('count', 0)} deals available")
                    click.echo(f"      WordPress ready: {deals.get('wordpress_ready', False)}")
                else:
                    click.echo(f"   ❌ WordPress deals test failed: {response.status_code}")
                
                # Test WordPress CTA config
                response = await client.get(f"{self.base_url}/wordpress/quote-cta")
                if response.status_code == 200:
                    cta = response.json()
                    click.echo(f"   ✅ WordPress CTA config: {cta.get('cta_config', {}).get('button_text')}")
                else:
                    click.echo(f"   ❌ WordPress CTA test failed: {response.status_code}")
                
                # Test GA4 analytics
                analytics_data = {
                    "event": "test_event",
                    "parameters": {"test": "true"},
                    "client_id": "test_client_123"
                }
                response = await client.post(f"{self.base_url}/analytics/track-event", json=analytics_data)
                if response.status_code == 200:
                    result = response.json()
                    click.echo(f"   ✅ GA4 Analytics: Event tracked with cross-domain support")
                else:
                    click.echo(f"   ❌ Analytics test failed: {response.status_code}")
                    
                return True
                
        except Exception as e:
            click.echo(f"   ❌ New features test error: {e}")
            return False

@click.group()
def cli():
    """SkyRide Wompi Integration Test Tool"""
    pass

@cli.command()
def health():
    """Test API health endpoint only"""
    async def run_health_test():
        tester = SkyRideWompiTester()
        await tester.test_api_health()
    
    asyncio.run(run_health_test())

@cli.command()
def listings():
    """Test listings endpoint only"""
    async def run_listings_test():
        tester = SkyRideWompiTester()
        await tester.test_listings()
    
    asyncio.run(run_listings_test())

@cli.command()
@click.option('--listing-id', help='Specific listing ID to test')
def quote(listing_id):
    """Test quote creation and retrieval"""
    async def run_quote_test():
        tester = SkyRideWompiTester()
        
        if not listing_id:
            click.echo("Getting listing ID from API...")
            listing_id_found = await tester.test_listings()
            if not listing_id_found:
                click.echo("❌ No listings found, cannot test quote creation")
                return
            listing_id = listing_id_found
        
        token = await tester.test_quote_creation(listing_id)
        if token:
            await tester.test_quote_retrieval(token)
    
    asyncio.run(run_quote_test())

@cli.command()
def full():
    """Run complete end-to-end test"""
    async def run_full_test():
        tester = SkyRideWompiTester()
        
        click.echo("🚀 SkyRide Wompi Integration - Full Test Suite")
        click.echo("=" * 50)
        
        # Test API health
        health_ok = await tester.test_api_health()
        if not health_ok:
            click.echo("❌ API health check failed, aborting tests")
            return
        
        click.echo()
        
        # Test listings
        listing_id = await tester.test_listings()
        if not listing_id:
            click.echo("❌ No listings found, aborting tests")
            return
        
        click.echo()
        
        # Test quote creation
        token = await tester.test_quote_creation(listing_id)
        if not token:
            click.echo("❌ Quote creation failed, aborting tests")
            return
        
        click.echo()
        
        # Test quote retrieval
        quote_ok = await tester.test_quote_retrieval(token)
        if not quote_ok:
            click.echo("❌ Quote retrieval failed, aborting tests")
            return
        
        click.echo()
        
        # Test hold creation
        hold_id = await tester.test_hold_creation(token)
        if not hold_id:
            click.echo("❌ Hold creation failed, skipping checkout test")
            return
        
        click.echo()
        
        # Test checkout (use quote ID as order ID for demo)
        payment_link = await tester.test_checkout(token)
        
        click.echo()
        click.echo("📊 Test Summary:")
        click.echo(f"   API Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
        click.echo(f"   Listings: {'✅ PASS' if listing_id else '❌ FAIL'}")
        click.echo(f"   Quote Creation: {'✅ PASS' if token else '❌ FAIL'}")
        click.echo(f"   Quote Retrieval: {'✅ PASS' if quote_ok else '❌ FAIL'}")
        click.echo(f"   Hold Creation: {'✅ PASS' if hold_id else '❌ FAIL'}")
        click.echo(f"   Checkout: {'✅ PASS' if payment_link else '❌ FAIL'}")
        
        if all([health_ok, listing_id, token, quote_ok, hold_id, payment_link]):
            click.echo("\n🎉 All tests passed! Platform is ready for use.")
        else:
            click.echo("\n⚠️  Some tests failed. Check configuration and try again.")
    
    asyncio.run(run_full_test())

@cli.command()
@click.option('--url', default='https://charter-hub-1.preview.emergentagent.com', help='Frontend URL to test')
def frontend(url):
    """Test frontend accessibility"""
    async def test_frontend():
        click.echo(f"🌐 Testing Frontend: {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    click.echo(f"   ✅ Frontend accessible")
                    click.echo(f"      Status: {response.status_code}")
                    click.echo(f"      Content-Type: {response.headers.get('content-type')}")
                    
                    # Check if it contains SkyRide content
                    if 'SkyRide' in response.text:
                        click.echo(f"      ✅ SkyRide content detected")
                    else:
                        click.echo(f"      ⚠️  SkyRide content not detected")
                else:
                    click.echo(f"   ❌ Frontend not accessible: {response.status_code}")
                    
        except Exception as e:
            click.echo(f"   ❌ Frontend test error: {e}")
    
    asyncio.run(test_frontend())

@cli.command()
def info():
    """Show configuration information"""
    click.echo("ℹ️  SkyRide Configuration Information")
    click.echo("=" * 40)
    click.echo(f"API Base URL: https://charter-hub-1.preview.emergentagent.com/api")
    click.echo(f"Frontend URL: https://charter-hub-1.preview.emergentagent.com")
    click.echo(f"DRY_RUN Mode: {os.getenv('DRY_RUN', 'true')}")
    click.echo(f"Wompi Environment: {os.getenv('WOMPI_ENV', 'test')}")
    
    # Check if keys are configured
    click.echo("\n🔑 API Keys Status:")
    click.echo(f"   Wompi Public Key: {'✅ Configured' if os.getenv('WOMPI_PUBLIC_KEY') != '__PROVIDED__' else '❌ Not configured'}")
    click.echo(f"   Wompi Private Key: {'✅ Configured' if os.getenv('WOMPI_PRIVATE_KEY') != '__PROVIDED__' else '❌ Not configured'}")
    click.echo(f"   Wompi Webhook Secret: {'✅ Configured' if os.getenv('WOMPI_WEBHOOK_SECRET') != '__PROVIDED__' else '❌ Not configured'}")
    
    click.echo("\n📚 Available Test Commands:")
    click.echo("   python cli_test_wompi.py health     - Test API health")
    click.echo("   python cli_test_wompi.py listings   - Test listings endpoint")
    click.echo("   python cli_test_wompi.py quote      - Test quote creation")
    click.echo("   python cli_test_wompi.py frontend   - Test frontend accessibility")
    click.echo("   python cli_test_wompi.py full       - Run complete test suite")

if __name__ == '__main__':
    cli()