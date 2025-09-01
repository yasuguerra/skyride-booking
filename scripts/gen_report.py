#!/usr/bin/env python3
"""
SkyRide Operations Report Generator
Generates comprehensive health and status report for v2.0
"""

import asyncio
import aiohttp
import json
import subprocess
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import redis.asyncio as aioredis
import asyncpg

# Configuration
API_BASE = os.getenv('BASE_URL', 'https://booking.skyride.city')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://skyride_user:skyride_password@localhost:5432/skyride')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class SkyRideReportGenerator:
    """Generate comprehensive operations report."""
    
    def __init__(self):
        self.report_data = {}
        self.errors = []
    
    async def generate_report(self):
        """Generate the complete operations report."""
        print("🔍 Generating SkyRide v2.0 Operations Report...")
        
        # Run all health checks
        await asyncio.gather(
            self.check_api_health(),
            self.check_database_health(),
            self.check_redis_health(),
            self.check_imports_status(),
            self.test_pricing_engine(),
            self.test_availability_system(),
            self.test_holds_system(),
            self.test_webhook_system(),
            self.test_whatsapp_integration(),
            self.test_widget_system(),
            self.check_analytics_setup(),
            return_exceptions=True
        )
        
        # Generate report content
        report_content = self.format_report()
        
        # Write to file
        report_file = f"REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"📊 Report generated: {report_file}")
        return report_file
    
    async def check_api_health(self):
        """Check API health and response times."""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                async with session.get(f"{API_BASE}/api/health") as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        self.report_data['api_health'] = {
                            'status': 'healthy',
                            'response_time_ms': round(response_time, 2),
                            'data': data
                        }
                    else:
                        self.report_data['api_health'] = {
                            'status': 'unhealthy',
                            'response_time_ms': round(response_time, 2),
                            'status_code': response.status
                        }
        except Exception as e:
            self.report_data['api_health'] = {'status': 'error', 'error': str(e)}
            self.errors.append(f"API health check failed: {e}")
    
    async def check_database_health(self):
        """Check PostgreSQL database health."""
        try:
            conn = await asyncpg.connect(POSTGRES_URL)
            
            # Get database info
            version = await conn.fetchval('SELECT version()')
            db_size = await conn.fetchval('SELECT pg_size_pretty(pg_database_size(current_database()))')
            connections = await conn.fetchval('SELECT count(*) FROM pg_stat_activity')
            
            # Get table counts
            tables = await conn.fetch("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
                FROM pg_stat_user_tables 
                ORDER BY schemaname, tablename
            """)
            
            await conn.close()
            
            self.report_data['database'] = {
                'status': 'connected',
                'version': version,
                'size': db_size,
                'connections': connections,
                'tables': [dict(row) for row in tables]
            }
            
        except Exception as e:
            self.report_data['database'] = {'status': 'error', 'error': str(e)}
            self.errors.append(f"Database check failed: {e}")
    
    async def check_redis_health(self):
        """Check Redis cache health."""
        try:
            redis = aioredis.from_url(REDIS_URL)
            
            # Get Redis info
            info = await redis.info()
            memory_info = await redis.info('memory')
            
            # Count active holds
            hold_keys = await redis.keys('hold:*')
            active_holds = len(hold_keys)
            
            await redis.close()
            
            self.report_data['redis'] = {
                'status': 'connected',
                'version': info['redis_version'],
                'memory_used': memory_info['used_memory_human'],
                'memory_peak': memory_info['used_memory_peak_human'],
                'active_holds': active_holds,
                'uptime_seconds': info['uptime_in_seconds']
            }
            
        except Exception as e:
            self.report_data['redis'] = {'status': 'error', 'error': str(e)}
            self.errors.append(f"Redis check failed: {e}")
    
    async def check_imports_status(self):
        """Check for recent import error files."""
        try:
            import_errors = []
            current_dir = Path('.')
            
            # Look for import error files
            for error_file in current_dir.glob('import_errors_*.csv'):
                stat = error_file.stat()
                import_errors.append({
                    'file': error_file.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            self.report_data['imports'] = {
                'error_files': import_errors,
                'status': 'no_recent_errors' if not import_errors else 'errors_found'
            }
            
        except Exception as e:
            self.report_data['imports'] = {'status': 'error', 'error': str(e)}
    
    async def test_pricing_engine(self):
        """Test pricing calculation."""
        try:
            async with aiohttp.ClientSession() as session:
                quote_data = {
                    "origin": "PTY",
                    "destination": "BLB", 
                    "date": "2025-01-15",
                    "passengers": 2
                }
                
                async with session.post(f"{API_BASE}/api/quotes", json=quote_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.report_data['pricing'] = {
                            'status': 'working',
                            'test_quote': data.get('breakdown', {}),
                            'token': data.get('token', 'N/A')
                        }
                    else:
                        self.report_data['pricing'] = {
                            'status': 'failed',
                            'status_code': response.status,
                            'error': await response.text()
                        }
                        
        except Exception as e:
            self.report_data['pricing'] = {'status': 'error', 'error': str(e)}
    
    async def test_availability_system(self):
        """Test availability system."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{API_BASE}/api/availability?dateRange=2025-01-01..2025-01-31"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.report_data['availability'] = {
                            'status': 'working',
                            'summary': data.get('summary', {}),
                            'total_slots': len(data.get('slots', []))
                        }
                    else:
                        self.report_data['availability'] = {
                            'status': 'failed',
                            'status_code': response.status
                        }
        except Exception as e:
            self.report_data['availability'] = {'status': 'error', 'error': str(e)}
    
    async def test_holds_system(self):
        """Test holds creation with idempotency."""
        try:
            async with aiohttp.ClientSession() as session:
                hold_data = {
                    "listing_id": f"test_listing_{int(datetime.now().timestamp())}",
                    "customer_email": "test@skyride.city"
                }
                
                headers = {
                    "Idempotency-Key": f"test-{int(datetime.now().timestamp())}"
                }
                
                async with session.post(f"{API_BASE}/api/holds", json=hold_data, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.report_data['holds'] = {
                            'status': 'working',
                            'test_hold': {
                                'hold_id': data.get('hold_id'),
                                'expires_at': data.get('expires_at'),
                                'remaining_seconds': data.get('remaining_seconds')
                            }
                        }
                    else:
                        self.report_data['holds'] = {
                            'status': 'failed',
                            'status_code': response.status
                        }
        except Exception as e:
            self.report_data['holds'] = {'status': 'error', 'error': str(e)}
    
    async def test_webhook_system(self):
        """Check webhook system status."""
        # This would typically check recent webhook events from the database
        self.report_data['webhooks'] = {
            'status': 'configured',
            'note': 'Manual verification required for webhook delivery'
        }
    
    async def test_whatsapp_integration(self):
        """Test WhatsApp template system."""
        try:
            async with aiohttp.ClientSession() as session:
                template_data = {
                    "template": "quote_created",
                    "to": "+507-6000-0000",
                    "params": {
                        "customer_name": "Test Customer",
                        "quote_amount": "2500"
                    }
                }
                
                async with session.post(f"{API_BASE}/api/wa/send-template", json=template_data) as response:
                    self.report_data['whatsapp'] = {
                        'status': 'configured' if response.status == 200 else 'failed',
                        'status_code': response.status
                    }
        except Exception as e:
            self.report_data['whatsapp'] = {'status': 'error', 'error': str(e)}
    
    async def test_widget_system(self):
        """Test widget availability."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/widget.js") as response:
                    self.report_data['widget'] = {
                        'status': 'available' if response.status == 200 else 'unavailable',
                        'status_code': response.status,
                        'size_bytes': len(await response.read()) if response.status == 200 else 0
                    }
        except Exception as e:
            self.report_data['widget'] = {'status': 'error', 'error': str(e)}
    
    async def check_analytics_setup(self):
        """Check analytics configuration."""
        ga4_id = os.getenv('GA_MEASUREMENT_ID', 'Not configured')
        self.report_data['analytics'] = {
            'ga4_measurement_id': ga4_id,
            'status': 'configured' if ga4_id != 'Not configured' else 'not_configured'
        }
    
    def format_report(self):
        """Format the report data into markdown."""
        now = datetime.now(timezone.utc)
        
        report = f"""# SkyRide v2.0 Operations Report

**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Environment:** Production  
**PostgreSQL/Redis Stack**

## System Health

### Database Status
- PostgreSQL connection: {'✅ Connected' if self.report_data.get('database', {}).get('status') == 'connected' else '❌ Error'}
- Database version: {self.report_data.get('database', {}).get('version', 'Unknown')}
- Database size: {self.report_data.get('database', {}).get('size', 'Unknown')}
- Active connections: {self.report_data.get('database', {}).get('connections', 'Unknown')}

### Redis Cache Status  
- Redis connection: {'✅ Connected' if self.report_data.get('redis', {}).get('status') == 'connected' else '❌ Error'}
- Redis version: {self.report_data.get('redis', {}).get('version', 'Unknown')}
- Memory usage: {self.report_data.get('redis', {}).get('memory_used', 'Unknown')}
- Active holds: {self.report_data.get('redis', {}).get('active_holds', 'Unknown')}

### API Health
- Backend health check: {'✅ Healthy' if self.report_data.get('api_health', {}).get('status') == 'healthy' else '❌ Unhealthy'}
- Response time: {self.report_data.get('api_health', {}).get('response_time_ms', 'Unknown')} ms

## Pricing & Quotes

### Quote Generation Test
**Result:**
```json
{json.dumps(self.report_data.get('pricing', {}).get('test_quote', {}), indent=2)}
```

## Availability & Holds

### Availability Check
**Result:**
- Status: {'✅ Working' if self.report_data.get('availability', {}).get('status') == 'working' else '❌ Failed'}
- Total slots: {self.report_data.get('availability', {}).get('total_slots', 'Unknown')}

### Active Holds Test
**Hold Test Result:**
- Status: {'✅ Working' if self.report_data.get('holds', {}).get('status') == 'working' else '❌ Failed'}
- Test hold ID: {self.report_data.get('holds', {}).get('test_hold', {}).get('hold_id', 'N/A')}

## Integration Status

### WhatsApp Templates
- Status: {'✅ Working' if self.report_data.get('whatsapp', {}).get('status') == 'configured' else '❌ Failed'}

### Widget System
- Widget availability: {'✅ Available' if self.report_data.get('widget', {}).get('status') == 'available' else '❌ Unavailable'}
- Widget size: {self.report_data.get('widget', {}).get('size_bytes', 0)} bytes

### Analytics (GA4)
- GA4 Measurement ID: {self.report_data.get('analytics', {}).get('ga4_measurement_id', 'Not configured')}
- Status: {'✅ Configured' if self.report_data.get('analytics', {}).get('status') == 'configured' else '⚠️ Not configured'}

## Errors Detected

"""
        
        if self.errors:
            for error in self.errors:
                report += f"- ❌ {error}\n"
        else:
            report += "- ✅ No errors detected\n"
        
        report += f"""
---

**Report generated by:** `scripts/gen_report.py`  
**Next report:** Scheduled daily  
**Contact:** SkyRide Operations Team
"""
        
        return report

async def main():
    """Main function to generate the report."""
    generator = SkyRideReportGenerator()
    report_file = await generator.generate_report()
    
    print(f"\n📋 Report Summary:")
    print(f"   - API Health: {generator.report_data.get('api_health', {}).get('status', 'Unknown')}")
    print(f"   - Database: {generator.report_data.get('database', {}).get('status', 'Unknown')}")
    print(f"   - Redis: {generator.report_data.get('redis', {}).get('status', 'Unknown')}")
    print(f"   - Pricing: {generator.report_data.get('pricing', {}).get('status', 'Unknown')}")
    print(f"   - Widget: {generator.report_data.get('widget', {}).get('status', 'Unknown')}")
    print(f"   - Errors: {len(generator.errors)}")
    
    if generator.errors:
        print(f"\n⚠️ Issues detected:")
        for error in generator.errors:
            print(f"   - {error}")
    
    return report_file

if __name__ == "__main__":
    asyncio.run(main())
