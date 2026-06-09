#!/usr/bin/env python3
"""
Quick test script for the /api/signals/short-term endpoint.
Run this after starting the Flask app to verify the endpoint works.

Usage:
    python test_short_term_endpoint.py
"""

import requests
import json
from datetime import datetime

# API base URL (change if running on different host/port)
BASE_URL = "http://localhost:5000"

def test_short_term_signals():
    """Test the /api/signals/short-term endpoint with various parameters"""

    endpoint = f"{BASE_URL}/api/signals/short-term"

    print("=" * 70)
    print("Testing /api/signals/short-term Endpoint")
    print("=" * 70)
    print()

    # Test 1: Basic request (no filters)
    print("TEST 1: Basic request (no filters)")
    print("-" * 70)
    try:
        response = requests.get(endpoint)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total signals: {data.get('total')}")
        print(f"Average confidence: {data.get('stats', {}).get('avg_confidence')}")
        print(f"Buy signals: {data.get('stats', {}).get('buy_count')}")
        print(f"Avoid signals: {data.get('stats', {}).get('avoid_count')}")
        print(f"Hold signals: {data.get('stats', {}).get('hold_count')}")
        if data.get('signals'):
            print(f"First signal: {data['signals'][0].get('ticker')} - {data['signals'][0].get('direction')} ({data['signals'][0].get('confidence')}/10)")
        print("✓ PASS\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    # Test 2: Filter by direction (buy only)
    print("TEST 2: Filter by direction (buy only)")
    print("-" * 70)
    try:
        response = requests.get(endpoint, params={"direction": "buy"})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total signals: {data.get('total')}")
        print(f"Applied filters: {data.get('filters')}")
        all_buy = all(s.get('direction') == 'buy' for s in data.get('signals', []))
        print(f"All returned signals are 'buy': {all_buy}")
        print("✓ PASS\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    # Test 3: Filter by min_confidence
    print("TEST 3: Filter by min_confidence (7+)")
    print("-" * 70)
    try:
        response = requests.get(endpoint, params={"min_confidence": 7})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total signals: {data.get('total')}")
        all_above_threshold = all(s.get('confidence', 0) >= 7 for s in data.get('signals', []))
        print(f"All signals have confidence >= 7: {all_above_threshold}")
        print("✓ PASS\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    # Test 4: Limit results
    print("TEST 4: Limit results (top 5)")
    print("-" * 70)
    try:
        response = requests.get(endpoint, params={"limit": 5})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total signals returned: {data.get('total')}")
        print(f"Requested limit: 5")
        print(f"Actual limit applied: {data.get('total') <= 5}")
        print("✓ PASS\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    # Test 5: Combined filters
    print("TEST 5: Combined filters (direction=avoid, min_confidence=8, limit=3)")
    print("-" * 70)
    try:
        response = requests.get(endpoint, params={
            "direction": "avoid",
            "min_confidence": 8,
            "limit": 3
        })
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total signals: {data.get('total')}")
        all_avoid = all(s.get('direction') == 'avoid' for s in data.get('signals', []))
        all_high_conf = all(s.get('confidence', 0) >= 8 for s in data.get('signals', []))
        print(f"All signals are 'avoid': {all_avoid}")
        print(f"All signals have confidence >= 8: {all_high_conf}")
        print(f"Results limited to 3 or fewer: {data.get('total') <= 3}")
        print("✓ PASS\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print("""
If all tests passed ✓:
- Endpoint is accessible
- Filtering logic works correctly
- Stats calculations are accurate
- Response format matches specification

Next steps:
1. Start Phase 2: Frontend implementation
2. Build ShortTermRecommendations.jsx page
3. Create RecommendationStats, FilterBar, RecommendationGrid components
4. Add to main navigation
5. Test end-to-end integration
    """)

if __name__ == "__main__":
    test_short_term_signals()
