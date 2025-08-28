"""
Concurrency tests for holds system.
Tests race conditions when multiple requests try to hold the same listing.
"""
import asyncio
import pytest
import httpx
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TestHoldsConcurrency:
    """Test concurrent hold creation scenarios."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API calls."""
        return "http://localhost:8001"
    
    @pytest.fixture
    def test_listing_id(self):
        """Test listing ID for concurrency tests."""
        timestamp = int(datetime.now().timestamp())
        return f"test_listing_{timestamp}"
    
    @pytest.fixture
    def hold_request_data(self, test_listing_id):
        """Standard hold request data."""
        return {
            "listing_id": test_listing_id,
            "customer_email": "test@skyride.city",
            "customer_phone": "+507-6123-4567",
            "duration_minutes": 60  # 1 hour for testing
        }
    
    async def create_hold_request(self, client: httpx.AsyncClient, base_url: str, data: dict, headers: dict = None):
        """Helper to create a hold request."""
        try:
            response = await client.post(
                f"{base_url}/api/holds",
                json=data,
                headers=headers or {}
            )
            return {
                "status_code": response.status_code,
                "response": response.json() if response.status_code != 500 else None,
                "success": response.status_code in [200, 201]
            }
        except Exception as e:
            logger.error(f"Error in hold request: {e}")
            return {
                "status_code": 500,
                "response": None,
                "success": False,
                "error": str(e)
            }
    
    @pytest.mark.asyncio
    async def test_concurrent_hold_creation_race_condition(self, base_url, hold_request_data):
        """
        Test that only one of two simultaneous hold requests succeeds.
        This tests the core race condition protection.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create two simultaneous requests for the same listing
            task1 = self.create_hold_request(client, base_url, hold_request_data)
            task2 = self.create_hold_request(client, base_url, hold_request_data)
            
            # Execute both requests concurrently
            results = await asyncio.gather(task1, task2, return_exceptions=True)
            
            # Analyze results
            successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
            
            # Assertions
            assert len(successful_requests) == 1, f"Expected exactly 1 successful request, got {len(successful_requests)}"
            assert len(failed_requests) == 1, f"Expected exactly 1 failed request, got {len(failed_requests)}"
            
            # Check that successful request got 200/201
            success_result = successful_requests[0]
            assert success_result["status_code"] in [200, 201], f"Successful request should return 200/201, got {success_result['status_code']}"
            
            # Check that failed request got 409 (Conflict)
            failed_result = failed_requests[0]
            assert failed_result["status_code"] == 409, f"Failed request should return 409, got {failed_result['status_code']}"
            
            logger.info("✅ Concurrency test passed: Only one hold created successfully")
    
    @pytest.mark.asyncio
    async def test_idempotency_key_behavior(self, base_url, hold_request_data):
        """
        Test that requests with the same idempotency key return the same result.
        """
        idempotency_key = f"test_key_{datetime.now().isoformat()}"
        headers = {"Idempotency-Key": idempotency_key}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create first request
            result1 = await self.create_hold_request(client, base_url, hold_request_data, headers)
            
            # Create second request with same idempotency key
            result2 = await self.create_hold_request(client, base_url, hold_request_data, headers)
            
            # Both should be successful
            assert result1["success"], f"First request failed: {result1}"
            assert result2["success"], f"Second request failed: {result2}"
            
            # Second request should indicate it came from idempotency cache
            assert result2["response"].get("created_from_idempotency") is True, "Second request should be from idempotency cache"
            
            # Hold IDs should be the same
            assert result1["response"]["hold_id"] == result2["response"]["hold_id"], "Hold IDs should match for idempotent requests"
            
            logger.info("✅ Idempotency test passed: Same result returned for same key")
    
    @pytest.mark.asyncio
    async def test_different_listings_no_conflict(self, base_url, hold_request_data):
        """
        Test that holds on different listings don't conflict.
        """
        # Create two different listing IDs
        data1 = hold_request_data.copy()
        data2 = hold_request_data.copy()
        data2["listing_id"] = f"{hold_request_data['listing_id']}_different"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create concurrent requests for different listings
            task1 = self.create_hold_request(client, base_url, data1)
            task2 = self.create_hold_request(client, base_url, data2)
            
            results = await asyncio.gather(task1, task2, return_exceptions=True)
            
            # Both should succeed
            successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
            assert len(successful_requests) == 2, f"Expected 2 successful requests, got {len(successful_requests)}"
            
            logger.info("✅ Different listings test passed: No conflicts between different listings")
    
    @pytest.mark.asyncio 
    async def test_hold_release_and_recreate(self, base_url, hold_request_data):
        """
        Test that a hold can be released and then recreated.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create initial hold
            create_result = await self.create_hold_request(client, base_url, hold_request_data)
            assert create_result["success"], f"Initial hold creation failed: {create_result}"
            
            listing_id = hold_request_data["listing_id"]
            
            # Release the hold
            release_response = await client.delete(f"{base_url}/api/holds/{listing_id}")
            assert release_response.status_code == 200, f"Hold release failed: {release_response.status_code}"
            
            # Create hold again
            recreate_result = await self.create_hold_request(client, base_url, hold_request_data)
            assert recreate_result["success"], f"Hold recreation failed: {recreate_result}"
            
            logger.info("✅ Release and recreate test passed: Hold successfully released and recreated")
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, base_url, hold_request_data):
        """
        Stress test with multiple concurrent requests to ensure system stability.
        """
        num_requests = 10
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create multiple concurrent requests
            tasks = [
                self.create_hold_request(client, base_url, hold_request_data)
                for _ in range(num_requests)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful and failed requests
            successful = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
            
            # Should have exactly 1 success and (num_requests - 1) failures
            assert len(successful) == 1, f"Expected exactly 1 successful request, got {len(successful)}"
            assert len(failed) == num_requests - 1, f"Expected {num_requests - 1} failed requests, got {len(failed)}"
            
            # All failed requests should be 409 Conflict
            for failed_request in failed:
                assert failed_request["status_code"] == 409, f"Failed request should return 409, got {failed_request['status_code']}"
            
            logger.info(f"✅ Stress test passed: 1 success out of {num_requests} concurrent requests")
