import requests
import sys
from datetime import datetime
import json

class CharterSystemAPITester:
    def __init__(self, base_url="https://flightops-central.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failures.append(f"{name}: Expected {expected_status}, got {response.status_code}")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failures.append(f"{name}: {str(e)}")
            return False, {}

    def test_basic_endpoints(self):
        """Test basic endpoints that should exist"""
        print("\n=== Testing Basic Endpoints ===")
        
        # Test root endpoint
        self.run_test("Root Endpoint", "GET", "api/", 200)
        
        # Test status endpoints
        self.run_test("Get Status Checks", "GET", "api/status", 200)
        
        # Test creating a status check
        test_data = {"client_name": "test_client"}
        self.run_test("Create Status Check", "POST", "api/status", 200, test_data)

    def test_charter_system_endpoints(self):
        """Test charter system specific endpoints that frontend expects"""
        print("\n=== Testing Charter System Endpoints ===")
        
        # Test health endpoint (expected by frontend)
        self.run_test("Health Check", "GET", "api/health", 200)
        
        # Test import endpoints (expected by frontend)
        self.run_test("Import Operators", "GET", "api/admin/import/operators", 405)  # Should exist but reject GET
        self.run_test("Import Aircraft", "GET", "api/admin/import/aircraft", 405)   # Should exist but reject GET
        self.run_test("Import Flights", "GET", "api/admin/import/flights", 405)     # Should exist but reject GET
        
        # Test quote creation (expected by frontend)
        quote_data = {
            "listing_id": "31c2934e-663d-493e-bab5-20a3a359f1dc",
            "departure_date": "2024-12-01",
            "passengers": 4
        }
        self.run_test("Create Quote", "POST", "api/quotes", 200, quote_data)

    def test_database_connectivity(self):
        """Test if database operations work"""
        print("\n=== Testing Database Connectivity ===")
        
        # Create multiple status checks to test database
        for i in range(3):
            test_data = {"client_name": f"test_client_{i}"}
            success, response = self.run_test(f"Create Status Check {i+1}", "POST", "api/status", 200, test_data)
            
        # Get all status checks to verify database persistence
        success, response = self.run_test("Verify Database Persistence", "GET", "api/status", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} status checks in database")

def main():
    print("🚀 Starting Charter Aviation System API Tests")
    print("=" * 60)
    
    tester = CharterSystemAPITester()
    
    # Test basic functionality that exists
    tester.test_basic_endpoints()
    
    # Test charter system functionality that frontend expects
    tester.test_charter_system_endpoints()
    
    # Test database connectivity
    tester.test_database_connectivity()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    
    if tester.failures:
        print("\n❌ FAILURES:")
        for failure in tester.failures:
            print(f"  - {failure}")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())