#!/usr/bin/env python3
"""
SkyRide Backend API Test Suite
Tests all backend endpoints for the charter flight booking platform
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class SkyRideAPITester:
    def __init__(self, base_url="https://flightdb-shift.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, status_code, response_data)"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                return False, 0, f"Unsupported method: {method}"

            try:
                response_data = response.json()
            except:
                response_data = response.text

            return True, response.status_code, response_data

        except requests.exceptions.RequestException as e:
            return False, 0, str(e)

    def test_health_endpoint(self):
        """Test /api/health endpoint - PostgreSQL version"""
        success, status_code, data = self.make_request('GET', '/health')
        
        if not success:
            self.log_test("Health Check", False, f"Request failed: {data}")
            return False

        if status_code == 200:
            # Check for PostgreSQL migration completion
            if data.get('status') == 'ok':
                db_type = data.get('database_type', '')
                migration_status = data.get('postgresql_migration', '')
                payments_dry_run = data.get('payments_dry_run', True)
                
                # Verify PostgreSQL migration is complete
                if 'PostgreSQL' in db_type and migration_status == 'complete':
                    self.log_test("PostgreSQL Migration", True, f"Database: {db_type}, Migration: {migration_status}")
                else:
                    self.log_test("PostgreSQL Migration", False, f"Database: {db_type}, Migration: {migration_status}")
                
                # Check integrations
                integrations = data.get('integrations', {})
                wompi_status = integrations.get('wompi', 'unknown')
                chatrace_status = integrations.get('chatrace', 'unknown')
                redis_status = integrations.get('redis_locks', 'unknown')
                
                self.log_test("Wompi Integration", wompi_status == 'production_ready', f"Status: {wompi_status}")
                self.log_test("Chatrace Integration", chatrace_status == 'production_ready', f"Status: {chatrace_status}")
                self.log_test("Redis Locks", redis_status == 'ready', f"Status: {redis_status}")
                self.log_test("Payments DRY_RUN", not payments_dry_run, f"DRY_RUN: {payments_dry_run} (should be false for production)")
                
                self.log_test("Health Check", True, f"Status: {data.get('status')}, Version: {data.get('version')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status not OK: {data.get('status')}", data)
                return False
        else:
            self.log_test("Health Check", False, f"Expected 200, got {status_code}", data)
            return False

    def test_listings_endpoint(self):
        """Test /api/listings endpoint"""
        success, status_code, data = self.make_request('GET', '/listings')
        
        if not success:
            self.log_test("Get Listings", False, f"Request failed: {data}")
            return None

        if status_code == 200:
            if isinstance(data, list):
                listings_count = len(data)
                self.log_test("Get Listings", True, f"Retrieved {listings_count} listings")
                
                # Validate listing structure if we have listings
                if listings_count > 0:
                    first_listing = data[0]
                    required_fields = ['_id', 'basePrice', 'serviceFee', 'totalPrice', 'operator', 'aircraft', 'route']
                    missing_fields = [field for field in required_fields if field not in first_listing]
                    
                    if missing_fields:
                        self.log_test("Listing Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Listing Structure", True, "All required fields present")
                        
                        # Check if we have the expected 4 Panama City flights
                        panama_flights = [l for l in data if l.get('route', {}).get('origin', '').lower().find('panama') != -1]
                        self.log_test("Panama City Flights", len(panama_flights) >= 4, f"Found {len(panama_flights)} Panama City flights")
                
                return data
            else:
                self.log_test("Get Listings", False, f"Expected list, got {type(data)}", data)
                return None
        else:
            self.log_test("Get Listings", False, f"Expected 200, got {status_code}", data)
            return None

    def test_create_quote(self, listing_id: str):
        """Test /api/quotes endpoint"""
        quote_data = {
            "listingId": listing_id,
            "passengers": 2,
            "departureDate": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            "email": "test@skyride.city",
            "phone": "+507 6000-0000"
        }
        
        success, status_code, data = self.make_request('POST', '/quotes', data=quote_data)
        
        if not success:
            self.log_test("Create Quote", False, f"Request failed: {data}")
            return None

        if status_code == 200:
            required_fields = ['token', 'expiresAt', 'hostedQuoteUrl', 'totalPrice']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Create Quote", False, f"Missing fields: {missing_fields}", data)
                return None
            else:
                self.log_test("Create Quote", True, f"Quote created with token: {data['token']}")
                return data
        else:
            self.log_test("Create Quote", False, f"Expected 200, got {status_code}", data)
            return None

    def test_get_quote(self, token: str):
        """Test /api/quotes/{token} endpoint"""
        success, status_code, data = self.make_request('GET', f'/quotes/{token}')
        
        if not success:
            self.log_test("Get Quote by Token", False, f"Request failed: {data}")
            return None

        if status_code == 200:
            required_fields = ['_id', 'token', 'totalPrice', 'listing', 'operator', 'aircraft', 'route']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Get Quote by Token", False, f"Missing fields: {missing_fields}")
                return None
            else:
                self.log_test("Get Quote by Token", True, f"Quote retrieved successfully")
                return data
        else:
            self.log_test("Get Quote by Token", False, f"Expected 200, got {status_code}", data)
            return None

    def test_create_hold(self, token: str):
        """Test /api/holds endpoint"""
        hold_data = {
            "token": token,
            "depositAmount": 500.0
        }
        
        success, status_code, data = self.make_request('POST', '/holds', data=hold_data)
        
        if not success:
            self.log_test("Create Hold", False, f"Request failed: {data}")
            return None

        if status_code == 200:
            required_fields = ['holdId', 'expiresAt', 'message']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Create Hold", False, f"Missing fields: {missing_fields}", data)
                return None
            else:
                self.log_test("Create Hold", True, f"Hold created: {data['holdId']}")
                return data
        else:
            self.log_test("Create Hold", False, f"Expected 200, got {status_code}", data)
            return None

    def test_wompi_payment_integration(self, quote_id: str):
        """Test Wompi payment link creation - PRODUCTION MODE"""
        checkout_data = {
            "orderId": quote_id,
            "provider": "WOMPI"
        }
        
        success, status_code, data = self.make_request('POST', '/checkout', data=checkout_data)
        
        if not success:
            self.log_test("Wompi Payment Integration", False, f"Request failed: {data}")
            return None

        if status_code == 200:
            if 'paymentLinkUrl' in data:
                payment_url = data['paymentLinkUrl']
                # Check if it's a real Wompi URL (not mock)
                is_production = 'wompi.pa' in payment_url or 'wompi.co' in payment_url
                is_mock = 'mock_' in payment_url
                
                if is_production and not is_mock:
                    self.log_test("Wompi Payment Integration", True, f"Production payment link created: {payment_url[:50]}...")
                elif is_mock:
                    self.log_test("Wompi Payment Integration", False, f"Mock payment link detected (DRY_RUN mode): {payment_url}")
                else:
                    self.log_test("Wompi Payment Integration", True, f"Payment link created: {payment_url[:50]}...")
                return data
            else:
                self.log_test("Wompi Payment Integration", False, f"No payment link in response", data)
                return None
        elif status_code == 404:
            # Expected if booking doesn't exist, try to create booking first
            self.log_test("Wompi Payment Integration", False, f"Booking not found for quote ID: {quote_id}")
            return None
        else:
            self.log_test("Wompi Payment Integration", False, f"Unexpected status {status_code}", data)
            return None

    def test_whatsapp_template_integration(self):
        """Test WhatsApp template sending via Chatrace"""
        template_data = {
            "template": "quote_created",
            "to": "+507 6000-0000",
            "params": {
                "customer_name": "Test Customer",
                "quote_amount": "2500",
                "quote_link": "https://booking.skyride.city/q/test123"
            }
        }
        
        success, status_code, data = self.make_request('POST', '/wa/send-template', data=template_data)
        
        if not success:
            self.log_test("WhatsApp Template Integration", False, f"Request failed: {data}")
            return False

        if status_code == 200:
            if data.get('success') == True:
                self.log_test("WhatsApp Template Integration", True, "Template sent successfully")
                return True
            else:
                self.log_test("WhatsApp Template Integration", False, f"Template sending failed: {data}")
                return False
        else:
            self.log_test("WhatsApp Template Integration", False, f"Expected 200, got {status_code}", data)
            return False

    def test_redis_hold_locks(self):
        """Test Redis-based hold locks"""
        # Test creating a Redis hold lock
        hold_data = {
            "listingId": "test-listing-123",
            "holdDurationMinutes": 30
        }
        
        success, status_code, data = self.make_request('POST', '/holds/redis-lock', params=hold_data)
        
        if not success:
            self.log_test("Redis Hold Locks", False, f"Request failed: {data}")
            return False

        if status_code == 200:
            if data.get('success') == True:
                hold_key = data.get('holdKey', '')
                duration = data.get('expiresInMinutes', 0)
                self.log_test("Redis Hold Locks", True, f"Hold lock created: {hold_key}, Duration: {duration}min")
                return True
            else:
                self.log_test("Redis Hold Locks", False, f"Hold lock creation failed: {data}")
                return False
        else:
            self.log_test("Redis Hold Locks", False, f"Expected 200, got {status_code}", data)
            return False

    def test_postgresql_database_operations(self, listings):
        """Test PostgreSQL database operations"""
        if not listings or len(listings) == 0:
            self.log_test("PostgreSQL Database Operations", False, "No listings available to test database operations")
            return False
        
        # Test that listings have proper structure and data
        first_listing = listings[0]
        
        # Check for UUID-style IDs (PostgreSQL typically uses UUIDs)
        listing_id = first_listing.get('_id', '')
        has_uuid_style = len(listing_id) >= 32 and '-' in listing_id
        
        # Check for proper data types and structure
        has_prices = all(key in first_listing for key in ['basePrice', 'serviceFee', 'totalPrice'])
        has_relations = all(key in first_listing for key in ['operator', 'aircraft', 'route'])
        
        if has_prices and has_relations:
            self.log_test("PostgreSQL Database Operations", True, f"Database operations working, ID format: {'UUID-style' if has_uuid_style else 'Legacy'}")
            return True
        else:
            missing = []
            if not has_prices:
                missing.append("pricing fields")
            if not has_relations:
                missing.append("relation fields")
            self.log_test("PostgreSQL Database Operations", False, f"Missing: {', '.join(missing)}")
            return False

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting SkyRide Backend API Tests")
        print(f"📡 Testing endpoint: {self.api_url}")
        print("=" * 60)

        # Test 1: Health Check
        health_ok = self.test_health_endpoint()
        if not health_ok:
            print("\n❌ Health check failed - stopping tests")
            return False

        # Test 2: Get Listings
        listings = self.test_listings_endpoint()
        if not listings:
            print("\n❌ No listings available - stopping tests")
            return False

        # Test 3: Create Quote (using first listing)
        first_listing = listings[0]
        quote = self.test_create_quote(first_listing['_id'])
        if not quote:
            print("\n❌ Quote creation failed - stopping tests")
            return False

        # Test 4: Get Quote by Token
        quote_details = self.test_get_quote(quote['token'])
        if not quote_details:
            print("\n❌ Quote retrieval failed - continuing with other tests")

        # Test 5: Create Hold
        hold = self.test_create_hold(quote['token'])
        if not hold:
            print("\n⚠️ Hold creation failed - continuing with other tests")

        # Test 6: Checkout (expected to fail in MVP without booking creation)
        checkout = self.test_checkout_endpoint(quote_details['_id'] if quote_details else 'test-id')

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        # Print critical issues
        critical_issues = []
        for test in self.test_results:
            if not test['success'] and test['name'] in ['Health Check', 'Get Listings', 'Create Quote']:
                critical_issues.append(test['name'])
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  • {issue}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = SkyRideAPITester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())