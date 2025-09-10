#!/usr/bin/env python3
"""
ZSPRD Portfolio Analytics API - Testing Examples
This script demonstrates how to test the API endpoints with sample data.
"""

import requests
import json
import asyncio
import aiohttp
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test user data (this would come from your NextAuth.js token in real usage)
TEST_USER_ID = "test-user-id-123"
TEST_JWT_TOKEN = "your-jwt-token-here"  # Replace with actual JWT token

# Request headers
HEADERS = {
    "Authorization": f"Bearer {TEST_JWT_TOKEN}",
    "Content-Type": "application/json"
}


class ZSPRDAPITester:
    """Test client for ZSPRD Portfolio Analytics API."""
    
    def __init__(self, base_url: str = API_BASE, token: Optional[str] = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def test_health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint."""
        print("\n🔍 Testing Health Check...")
        
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.json()
    
    def test_auth_endpoints(self) -> Dict[str, Any]:
        """Test authentication endpoints."""
        print("\n🔐 Testing Authentication...")
        
        # Test token validation (without actual token)
        print("Testing token validation...")
        auth_data = {"token": "dummy-token"}
        
        response = requests.post(f"{self.base_url}/auth/validate-token", 
                               json=auth_data)
        print(f"Token validation status: {response.status_code}")
        
        # Test getting current user profile (requires valid auth)
        if self.headers.get("Authorization"):
            response = requests.get(f"{self.base_url}/auth/me", 
                                  headers=self.headers)
            print(f"User profile status: {response.status_code}")
            if response.status_code == 200:
                print(f"User profile: {response.json()}")
        
        return {"auth_tested": True}
    
    def test_accounts_endpoints(self) -> Dict[str, str]:
        """Test accounts management."""
        print("\n🏦 Testing Accounts Management...")
        
        # Create a test account
        account_data = {
            "name": "Test Investment Account",
            "official_name": "Test Investment Account - Official",
            "type": "investment",
            "subtype": "brokerage",
            "currency": "USD",
            "mask": "1234"
        }
        
        print("Creating test account...")
        response = requests.post(f"{self.base_url}/accounts/", 
                               json=account_data, headers=self.headers)
        print(f"Create account status: {response.status_code}")
        
        account_id = None
        if response.status_code == 200:
            account = response.json()
            account_id = account["id"]
            print(f"Created account ID: {account_id}")
        
        # Get all accounts
        print("Getting all accounts...")
        response = requests.get(f"{self.base_url}/accounts/", headers=self.headers)
        print(f"Get accounts status: {response.status_code}")
        if response.status_code == 200:
            accounts = response.json()
            print(f"Found {len(accounts)} accounts")
        
        # Get specific account
        if account_id:
            print(f"Getting account {account_id}...")
            response = requests.get(f"{self.base_url}/accounts/{account_id}", 
                                  headers=self.headers)
            print(f"Get account status: {response.status_code}")
        
        return {"created_account_id": account_id}
    
    def test_securities_search(self) -> Dict[str, Any]:
        """Test securities search."""
        print("\n🔍 Testing Securities Search...")
        
        # Search for securities
        search_queries = ["AAPL", "SPY", "TSLA"]
        
        for query in search_queries:
            print(f"Searching for: {query}")
            response = requests.get(f"{self.base_url}/market-data/search/{query}", 
                                  headers=self.headers)
            print(f"Search status: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"Found {results['results_count']} results")
        
        return {"searches_completed": len(search_queries)}
    
    def test_holdings_management(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Test holdings management."""
        print("\n📊 Testing Holdings Management...")
        
        if not account_id:
            print("No account ID provided, skipping holdings tests")
            return {"skipped": True}
        
        # Create a test holding
        holding_data = {
            "account_id": account_id,
            "security_id": "dummy-security-id",  # Would be real security ID
            "quantity": 100.0,
            "cost_basis_per_share": 150.50,
            "cost_basis_total": 15050.0,
            "market_value": 16000.0,
            "currency": "USD",
            "as_of_date": date.today().isoformat()
        }
        
        print("Creating test holding...")
        response = requests.post(f"{self.base_url}/holdings/", 
                               json=holding_data, headers=self.headers)
        print(f"Create holding status: {response.status_code}")
        
        # Get all holdings
        print("Getting all holdings...")
        response = requests.get(f"{self.base_url}/holdings/", headers=self.headers)
        print(f"Get holdings status: {response.status_code}")
        if response.status_code == 200:
            holdings_data = response.json()
            print(f"Found {len(holdings_data.get('holdings', []))} holdings")
            print(f"Portfolio summary: ${holdings_data.get('summary', {}).get('total_market_value', 0):,.2f}")
        
        return {"holdings_tested": True}
    
    def test_transactions_management(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Test transactions management."""
        print("\n💰 Testing Transactions Management...")
        
        if not account_id:
            print("No account ID provided, skipping transactions tests")
            return {"skipped": True}
        
        # Create test transactions
        transactions = [
            {
                "account_id": account_id,
                "security_id": "dummy-security-id",
                "type": "buy",
                "side": "buy",
                "quantity": 100.0,
                "price": 150.50,
                "amount": 15050.0,
                "fees": 9.95,
                "trade_date": (date.today() - timedelta(days=30)).isoformat(),
                "transaction_currency": "USD",
                "description": "Purchase of test stock",
                "source": "manual"
            },
            {
                "account_id": account_id,
                "type": "dividend",
                "amount": 250.0,
                "trade_date": (date.today() - timedelta(days=15)).isoformat(),
                "transaction_currency": "USD",
                "description": "Quarterly dividend payment",
                "source": "manual"
            }
        ]
        
        created_transactions = []
        for txn_data in transactions:
            print(f"Creating {txn_data['type']} transaction...")
            response = requests.post(f"{self.base_url}/transactions/", 
                                   json=txn_data, headers=self.headers)
            print(f"Create transaction status: {response.status_code}")
            if response.status_code == 200:
                created_transactions.append(response.json())
        
        # Get all transactions
        print("Getting all transactions...")
        response = requests.get(f"{self.base_url}/transactions/", headers=self.headers)
        print(f"Get transactions status: {response.status_code}")
        if response.status_code == 200:
            transactions_data = response.json()
            print(f"Found {len(transactions_data.get('transactions', []))} transactions")
            
            summary = transactions_data.get('summary', {})
            print(f"Total invested: ${summary.get('total_invested', 0):,.2f}")
            print(f"Total fees: ${summary.get('total_fees', 0):,.2f}")
        
        # Get recent transactions
        print("Getting recent transactions...")
        response = requests.get(f"{self.base_url}/transactions/recent/", headers=self.headers)
        print(f"Recent transactions status: {response.status_code}")
        
        return {"transactions_created": len(created_transactions)}
    
    def test_analytics_endpoints(self) -> Dict[str, Any]:
        """Test analytics calculations."""
        print("\n📈 Testing Analytics...")
        
        # Test performance metrics
        print("Testing performance metrics...")
        response = requests.get(f"{self.base_url}/analytics/performance", 
                              headers=self.headers)
        print(f"Performance metrics status: {response.status_code}")
        if response.status_code == 200:
            performance = response.json()
            print(f"Total return: {performance.get('total_return', 0):.2f}%")
            print(f"Sharpe ratio: {performance.get('sharpe_ratio', 0):.3f}")
        
        # Test risk metrics
        print("Testing risk metrics...")
        response = requests.get(f"{self.base_url}/analytics/risk", 
                              headers=self.headers)
        print(f"Risk metrics status: {response.status_code}")
        if response.status_code == 200:
            risk = response.json()
            print(f"Beta: {risk.get('beta', 0):.3f}")
            print(f"VaR 95%: {risk.get('value_at_risk', {}).get('var_95', 0):.2f}%")
        
        # Test allocation breakdown
        print("Testing allocation breakdown...")
        response = requests.get(f"{self.base_url}/analytics/allocation", 
                              headers=self.headers)
        print(f"Allocation status: {response.status_code}")
        if response.status_code == 200:
            allocation = response.json()
            print(f"Portfolio value: ${allocation.get('total_portfolio_value', 0):,.2f}")
            print(f"Asset types: {list(allocation.get('by_asset_type', {}).keys())}")
        
        return {"analytics_tested": True}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run a comprehensive test of all endpoints."""
        print("🧪 Starting Comprehensive API Test")
        print("=" * 50)
        
        results = {}
        
        try:
            # Test health check
            results["health"] = self.test_health_check()
            
            # Test authentication
            results["auth"] = self.test_auth_endpoints()
            
            # Test accounts (and get account ID for other tests)
            account_results = self.test_accounts_endpoints()
            results["accounts"] = account_results
            account_id = account_results.get("created_account_id")
            
            # Test securities search
            results["securities"] = self.test_securities_search()
            
            # Test holdings (requires account)
            results["holdings"] = self.test_holdings_management(account_id)
            
            # Test transactions (requires account)
            results["transactions"] = self.test_transactions_management(account_id)
            
            # Test analytics
            results["analytics"] = self.test_analytics_endpoints()
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results["error"] = str(e)
        
        print("\n" + "=" * 50)
        print("🎉 Comprehensive Test Completed")
        print("Results Summary:")
        for component, result in results.items():
            status = "✅" if not result.get("error") and not result.get("skipped") else "❌"
            print(f"  {status} {component.capitalize()}: {result}")
        
        return results


def test_async_operations():
    """Test async operations like market data fetching."""
    print("\n🔄 Testing Async Operations...")
    
    async def fetch_market_data():
        async with aiohttp.ClientSession() as session:
            # Test market data refresh
            url = f"{API_BASE}/market-data/refresh-all"
            headers = {"Authorization": f"Bearer {TEST_JWT_TOKEN}"}
            
            async with session.post(url, headers=headers) as response:
                print(f"Market data refresh status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Refresh initiated for {data.get('securities_count', 0)} securities")
    
    # Run async test
    try:
        asyncio.run(fetch_market_data())
    except Exception as e:
        print(f"Async test error: {e}")


def generate_sample_csv_data():
    """Generate sample CSV data for import testing."""
    print("\n📄 Generating Sample CSV Data...")
    
    # Sample transactions CSV
    transactions_csv = """account_name,trade_date,symbol,transaction_type,side,quantity,price,amount,fees,currency,description
Investment Account,2024-01-15,AAPL,buy,buy,100,150.50,15050.00,9.95,USD,Apple stock purchase
Investment Account,2024-01-20,SPY,buy,buy,50,480.25,24012.50,9.95,USD,S&P 500 ETF purchase
Investment Account,2024-02-15,AAPL,dividend,,,,250.00,0.00,USD,Quarterly dividend
Investment Account,2024-03-10,AAPL,sell,sell,50,175.30,8765.00,9.95,USD,Partial Apple sale"""
    
    with open("sample_transactions.csv", "w") as f:
        f.write(transactions_csv)
    
    print("✅ Created sample_transactions.csv")
    
    # Sample holdings CSV
    holdings_csv = """account_name,symbol,quantity,avg_cost,currency
Investment Account,AAPL,50,150.50,USD
Investment Account,SPY,50,480.25,USD
Investment Account,TSLA,25,220.80,USD"""
    
    with open("sample_holdings.csv", "w") as f:
        f.write(holdings_csv)
    
    print("✅ Created sample_holdings.csv")


def main():
    """Main testing function."""
    print("🚀 ZSPRD Portfolio Analytics API Testing")
    print("=" * 60)
    
    # Initialize tester
    tester = ZSPRDAPITester(token=TEST_JWT_TOKEN if TEST_JWT_TOKEN != "your-jwt-token-here" else None)
    
    # Generate sample data
    generate_sample_csv_data()
    
    # Run comprehensive tests
    results = tester.run_comprehensive_test()
    
    # Test async operations
    test_async_operations()
    
    print("\n📋 Testing Complete!")
    print("\n💡 Next Steps:")
    print("1. Review any failed tests above")
    print("2. Check the API documentation at http://localhost:8000/api/v1/docs")
    print("3. Use the sample CSV files to test import functionality")
    print("4. Integrate these endpoints with your NextJS frontend")
    
    return results


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ Server not running. Please start the server first:")
        print("   python run_server.py")
        exit(1)
    
    main()