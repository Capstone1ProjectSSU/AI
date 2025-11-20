#!/usr/bin/env python3
"""
Simple test script for HiServer API
Run this after starting the server to verify it's working correctly.
"""

import requests
import time
import sys


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Health check passed")


def test_openapi():
    """Test OpenAPI documentation is accessible"""
    print("Testing OpenAPI docs...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200
    print("✓ OpenAPI docs accessible")


def poll_job_status(job_id: str, endpoint_prefix: str, timeout: int = 300):
    """Poll job status until completion or timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}{endpoint_prefix}/status/{job_id}")
        if response.status_code != 200:
            print(f"✗ Status check failed: {response.status_code}")
            return None

        data = response.json()
        status = data["status"]
        progress = data.get("progressPercent", 0)

        print(f"  Status: {status} ({progress}%)")

        if status == "completed":
            return data
        elif status == "failed":
            print(f"✗ Task failed: {data.get('error')}")
            return None

        time.sleep(2)

    print("✗ Task timed out")
    return None


def test_alternative_chord_recommendation():
    """Test synchronous alternative chord recommendation"""
    print("\nTesting alternative chord recommendation...")

    # Create a sample chord progression file
    import tempfile
    import json

    chord_data = {
        "key": "C major",
        "chords": [
            {"symbol": "C", "duration": 1.0},
            {"symbol": "F", "duration": 1.0},
            {"symbol": "G", "duration": 1.0},
            {"symbol": "C", "duration": 1.0}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(chord_data, f)
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            files = {'chord_file': f}
            data = {'chord_index': 1}  # F chord

            response = requests.post(
                f"{BASE_URL}/operations/alternative-chord-recommendation",
                files=files,
                data=data
            )

        if response.status_code == 200:
            result = response.json()
            print(f"  Original chord: {result['originalChord']}")
            print(f"  Alternatives found: {len(result['alternatives'])}")
            for alt in result['alternatives'][:3]:
                print(f"    - {alt['chord']} (confidence: {alt['confidence']:.2f})")
            print("✓ Alternative chord recommendation passed")
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Response: {response.text}")
    finally:
        import os
        os.unlink(temp_file)


def main():
    """Run all tests"""
    print("=" * 60)
    print("HiServer API Test Suite")
    print("=" * 60)

    try:
        # Basic connectivity tests
        test_health()
        test_openapi()

        # Test synchronous operation
        test_alternative_chord_recommendation()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print("\nThe server is working correctly.")
        print("Visit http://localhost:8000/docs for interactive API documentation.")

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server")
        print("Make sure the server is running: ./start_server.sh")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
