#!/usr/bin/env python3
"""
Test script to verify component-level caching system
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Test URLs from cached images
BACKGROUND_URL = "https://v3b.fal.media/files/b/elephant/3DPADWs6g0YEDs37PcEqs.png"
CHARACTER_URL = "https://v3b.fal.media/files/b/panda/zXl6Elz8nhXH9E56TGs17.png"
COLLECTIBLE_URL = "https://v3b.fal.media/files/b/kangaroo/kgbRo_3Y6ZkTC2-hY77XQ.png"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_cache_stats():
    """Get current cache statistics"""
    response = requests.get(f"{BASE_URL}/component-cache/stats")
    stats = response.json()
    print(f"Cache Stats: {stats['stats']['total_components']} components, {stats['stats']['total_size_mb']} MB")
    return stats['stats']

def clear_cache():
    """Clear component cache"""
    response = requests.delete(f"{BASE_URL}/component-cache")
    print(f"Cache cleared: {response.json()['message']}")

def generate_game(bg_url, char_url, coll_url=None, num_frames=8):
    """Generate a game and measure time"""
    payload = {
        "background_url": bg_url,
        "character_url": char_url,
        "collectible_url": coll_url,
        "num_frames": num_frames,
        "game_name": "Cache Test Game",
        "debug_options": {
            "show_platforms": False,
            "show_sprite_frames": True,
            "show_collectibles": True
        }
    }
    
    start = time.time()
    response = requests.post(f"{BASE_URL}/generate-game", json=payload)
    duration = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        html_size = len(data['game_html'])
        platforms = data['platforms_detected']
        print(f"✓ Generation complete in {duration:.2f}s")
        print(f"  HTML size: {html_size:,} bytes, Platforms: {platforms}")
        return duration, data
    else:
        print(f"✗ Error: {response.status_code} - {response.text[:200]}")
        return duration, None

def main():
    print_header("Component-Level Cache Test")
    
    # Test 1: Clear cache and generate (all misses)
    print_header("TEST 1: First Generation (All Cache Misses)")
    clear_cache()
    check_cache_stats()
    
    print("\nGenerating game for the first time...")
    time1, _ = generate_game(BACKGROUND_URL, CHARACTER_URL, COLLECTIBLE_URL)
    
    stats1 = check_cache_stats()
    print(f"  Background components: {stats1['background']}")
    print(f"  Character components: {stats1['character']}")
    print(f"  Collectible components: {stats1['collectible']}")
    
    # Test 2: Generate exact same game (all hits)
    print_header("TEST 2: Same Generation (All Cache Hits)")
    print("Generating exact same game...")
    time2, _ = generate_game(BACKGROUND_URL, CHARACTER_URL, COLLECTIBLE_URL)
    
    stats2 = check_cache_stats()
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n🚀 Speedup: {speedup:.1f}x faster ({time1:.2f}s → {time2:.2f}s)")
    
    # Test 3: Change only character (partial cache)
    print_header("TEST 3: Change Character Only (Partial Cache)")
    print("Using different character URL...")
    time3, _ = generate_game(
        BACKGROUND_URL,
        CHARACTER_URL.replace("panda", "tiger"),  # Different URL (will likely fail but tests cache)
        COLLECTIBLE_URL
    )
    
    stats3 = check_cache_stats()
    print(f"  Expected: Background and Collectible cached, Character new")
    
    # Test 4: Change only background (partial cache)
    print_header("TEST 4: Change Background Only (Partial Cache)")
    print("Using different background URL...")
    time4, _ = generate_game(
        BACKGROUND_URL.replace("elephant", "lion"),  # Different URL
        CHARACTER_URL,
        COLLECTIBLE_URL
    )
    
    stats4 = check_cache_stats()
    print(f"  Expected: Character and Collectible cached, Background new")
    
    # Test 5: Change frame count (invalidates character cache)
    print_header("TEST 5: Same Character with Different Frame Count")
    print("Using same character URL but 6 frames instead of 8...")
    time5, _ = generate_game(BACKGROUND_URL, CHARACTER_URL, COLLECTIBLE_URL, num_frames=6)
    
    stats5 = check_cache_stats()
    print(f"  Character components: {stats5['character']} (should have 2: 8-frame and 6-frame)")
    
    # Summary
    print_header("SUMMARY")
    print(f"Test 1 (All MISS):      {time1:.2f}s")
    print(f"Test 2 (All HIT):       {time2:.2f}s - {speedup:.1f}x faster")
    print(f"Test 3 (Partial):       {time3:.2f}s")
    print(f"Test 4 (Partial):       {time4:.2f}s")
    print(f"Test 5 (Frame change):  {time5:.2f}s")
    print(f"\nFinal cache: {stats5['total_components']} components, {stats5['total_size_mb']} MB")
    
    print_header("✓ Component Cache Test Complete")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

