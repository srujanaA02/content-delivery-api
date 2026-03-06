import httpx
import time
import statistics
import json

BASE_URL = "http://localhost:3000"
REQUESTS = 50


def run_benchmark():
    print("🚀 Content Delivery API - Benchmark\n")

    # --- Upload a test file first ---
    print("📤 Uploading test file...")
    with open("testfile.txt", "rb") as f:
        upload_resp = httpx.post(
            f"{BASE_URL}/assets/upload",
            files={"file": ("bench.txt", f, "text/plain")}
        )
    asset = upload_resp.json()
    asset_id = asset["id"]
    etag = asset["etag"]
    print(f"✅ Uploaded: {asset_id}\n")

    # --- Benchmark normal downloads ---
    print(f"📥 Testing {REQUESTS} normal downloads...")
    times = []
    for _ in range(REQUESTS):
        start = time.time()
        r = httpx.get(f"{BASE_URL}/assets/{asset_id}/download")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    print(f"   Avg: {statistics.mean(times):.2f}ms")
    print(f"   Min: {min(times):.2f}ms")
    print(f"   Max: {max(times):.2f}ms\n")

    # --- Benchmark 304 responses ---
    print(f"⚡ Testing {REQUESTS} conditional requests (304)...")
    times_304 = []
    hits = 0
    for _ in range(REQUESTS):
        start = time.time()
        r = httpx.get(
            f"{BASE_URL}/assets/{asset_id}/download",
            headers={"If-None-Match": f'"{etag}"'}
        )
        elapsed = (time.time() - start) * 1000
        times_304.append(elapsed)
        if r.status_code == 304:
            hits += 1

    print(f"   Avg: {statistics.mean(times_304):.2f}ms")
    print(f"   304 Hit Rate: {hits}/{REQUESTS} ({(hits/REQUESTS)*100:.0f}%)\n")

    # --- Publish and test immutable ---
    print("📌 Publishing version...")
    pub = httpx.post(f"{BASE_URL}/assets/{asset_id}/publish").json()
    version_id = pub["version_id"]

    print(f"🔒 Testing immutable versioned URL...")
    r = httpx.get(f"{BASE_URL}/assets/public/{version_id}")
    cc = r.headers.get("cache-control", "")
    print(f"   Cache-Control: {cc}")
    print(f"   ✅ Immutable: {'immutable' in cc}\n")

    # --- Summary ---
    print("=" * 40)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 40)
    print(f"Normal Download Avg  : {statistics.mean(times):.2f}ms")
    print(f"Conditional Req Avg  : {statistics.mean(times_304):.2f}ms")
    print(f"304 Cache Hit Rate   : {(hits/REQUESTS)*100:.0f}%")
    print(f"Immutable Caching    : {'✅ YES' if 'immutable' in cc else '❌ NO'}")
    print("=" * 40)


if __name__ == "__main__":
    run_benchmark()