#!/usr/bin/env python3
"""
Test script for Gemini HTTP API Server
Tests all endpoints and functionality.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class HTTPAPITester:
    """Test the Gemini HTTP API server."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_health(self) -> bool:
        """Test health endpoint."""
        print("🏥 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Service: {data['service']}")
                print(f"   CDP Port: {data['config']['browser']['cdp_port']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_list_conversations(self) -> bool:
        """Test list conversations endpoint."""
        print("\n📚 Testing list conversations...")
        try:
            response = self.session.post(
                f"{self.base_url}/list",
                json={"include_metadata": True}
            )
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print(f"✅ Listed {data['count']} conversations")
                    for conv in data["conversations"][:3]:  # Show first 3
                        print(f"   📄 {conv['title']} ({conv['message_count']} messages)")
                    return True
                else:
                    print(f"❌ List failed: {data}")
                    return False
            else:
                print(f"❌ List request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ List error: {e}")
            return False
    
    def test_search_conversations(self) -> bool:
        """Test search conversations endpoint."""
        print("\n🔍 Testing search conversations...")
        try:
            response = self.session.post(
                f"{self.base_url}/search",
                json={"query": "memory", "limit": 5}
            )
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print(f"✅ Found {data['count']} conversations matching 'memory'")
                    for result in data["results"][:3]:  # Show first 3
                        print(f"   📄 {result['title']} (relevance: {result['relevance_score']}, matches: {result['message_matches']})")
                    return True
                else:
                    print(f"❌ Search failed: {data}")
                    return False
            else:
                print(f"❌ Search request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Search error: {e}")
            return False
    
    def test_analyze_conversations(self) -> bool:
        """Test analyze conversations endpoint."""
        print("\n📊 Testing analyze conversations...")
        try:
            response = self.session.post(
                f"{self.base_url}/analyze",
                json={"include_details": False}  # Just summary for test
            )
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    summary = data["data"]["summary"]
                    print(f"✅ Analysis completed")
                    print(f"   Total conversations: {summary['total_conversations']}")
                    print(f"   Total messages: {summary['total_messages']}")
                    print(f"   Avg messages/conversation: {summary['avg_messages_per_conversation']}")
                    return True
                else:
                    print(f"❌ Analysis failed: {data}")
                    return False
            else:
                print(f"❌ Analysis request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return False
    
    def test_tool_endpoint(self) -> bool:
        """Test generic tool endpoint."""
        print("\n🔧 Testing tool endpoint...")
        try:
            response = self.session.post(
                f"{self.base_url}/tool",
                json={
                    "tool": "search_conversations",
                    "arguments": {"query": "AI", "limit": 3}
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print(f"✅ Tool call successful")
                    print(f"   Found {data['count']} conversations matching 'AI'")
                    return True
                else:
                    print(f"❌ Tool call failed: {data}")
                    return False
            else:
                print(f"❌ Tool request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Tool error: {e}")
            return False
    
    def test_api_info(self) -> bool:
        """Test API info endpoint."""
        print("\n📋 Testing API info...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API info retrieved")
                print(f"   Service: {data['service']}")
                print(f"   Version: {data['version']}")
                print(f"   Status: {data['status']}")
                print(f"   Endpoints: {', '.join(data['endpoints'].keys())}")
                return True
            else:
                print(f"❌ API info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API info error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print(f"🚀 Testing Gemini HTTP API at {self.base_url}")
        print("=" * 60)
        
        tests = [
            self.test_api_info,
            self.test_health,
            self.test_list_conversations,
            self.test_search_conversations,
            self.test_analyze_conversations,
            self.test_tool_endpoint
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.5)  # Small delay between tests
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! HTTP API is working correctly.")
            return True
        else:
            print(f"❌ {total - passed} tests failed.")
            return False

def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Gemini HTTP API")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of the API")
    parser.add_argument("--wait", action="store_true", help="Wait for server to start")
    
    args = parser.parse_args()
    
    if args.wait:
        print("⏳ Waiting for server to start...")
        for i in range(10):
            try:
                response = requests.get(f"{args.url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    break
            except:
                pass
            time.sleep(1)
            print(f"   Attempt {i+1}/10...")
        else:
            print("❌ Server did not start in time")
            sys.exit(1)
    
    tester = HTTPAPITester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
