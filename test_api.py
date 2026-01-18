#!/usr/bin/env python3
"""
Simple test script for Voice Notes Service API.

Usage:
    python test_api.py <audio_file.m4a>
"""

import sys
import requests
from pathlib import Path


def test_health(base_url: str):
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{base_url}/api/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed!")
        print(f"   Status: {data['status']}")
        print(f"   Services: {data['services']}")
        print(f"   Vault: {data['vault']['repo']}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(response.text)
        return False


def test_voice(base_url: str, audio_file: str):
    """Test voice processing endpoint."""
    audio_path = Path(audio_file)

    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False

    print(f"\n🎤 Testing voice endpoint with: {audio_path.name}")

    with open(audio_path, 'rb') as f:
        files = {'audio': (audio_path.name, f, 'audio/m4a')}
        response = requests.post(f"{base_url}/api/voice", files=files)

    if response.status_code == 200:
        data = response.json()

        if data.get('success'):
            print("✅ Voice processing succeeded!")
            print(f"\n📝 Transcription:")
            print(f"   {data['transcription']}")

            if data.get('actions'):
                print(f"\n🔧 Actions performed ({len(data['actions'])}):")
                for i, action in enumerate(data['actions'], 1):
                    print(f"   {i}. {action['function']}")
                    print(f"      Result: {action['result']}")

            print(f"\n💬 Agent Summary:")
            print(f"   {data['agent_summary']}")
            return True
        else:
            print(f"❌ Processing failed: {data.get('error')}")
            print(f"   Details: {data.get('details')}")
            return False
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)
        return False


def main():
    """Main test function."""
    base_url = "http://localhost:8000"

    # Test health first
    if not test_health(base_url):
        print("\n⚠️  Health check failed. Is the server running?")
        print("   Run: uvicorn app.main:app --reload")
        return 1

    # Test voice if audio file provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if not test_voice(base_url, audio_file):
            return 1
    else:
        print("\n💡 To test voice processing, provide an audio file:")
        print("   python test_api.py test.m4a")

    print("\n✨ All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
