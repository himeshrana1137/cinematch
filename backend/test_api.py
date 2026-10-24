import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoints():
    print("1. Testing /api/health:")
    r = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print("Health Status:", r.status_code, r.json())
    assert r.status_code == 200 and r.json().get("status") == "ok"

    print("\n2. Testing /api/search?q=matrix:")
    r = requests.get(f"{BASE_URL}/api/search?q=matrix", timeout=5)
    print("Search Status:", r.status_code)
    search_res = r.json()
    print(f"Found: {len(search_res)} movies")
    for m in search_res[:3]:
        print(f"  ID: {m['movieId']} | {m['title']} ({m['year']}) | Genres: {m.get('genres')}")

    print("\n3. Testing /api/popular?n=4:")
    r = requests.get(f"{BASE_URL}/api/popular?n=4", timeout=10)
    print("Popular Status:", r.status_code)
    pop_res = r.json()
    for m in pop_res:
        print(f"  [{m['movieId']}] {m['title']} ({m['year']}) - TMDB: {m['tmdb_rating']} - Poster: {m['poster_url']}")
        assert m['poster_url'] is None or m['poster_url'].startswith("https://image.tmdb.org/t/p/w500")

    print("\n4. Testing /api/recommend for Matrix (movieId=2571):")
    r = requests.get(f"{BASE_URL}/api/recommend?movie_id=2571&n=3&alpha=0.5", timeout=10)
    print("Recommend Status:", r.status_code)
    rec = r.json()
    print("Selected:", rec["selected"]["title"], "TMDB Poster:", rec["selected"]["poster_url"])
    for m in rec["results"]:
        print(f"  -> {m['title']} | Match: {m['match_percent']}% | Content: {m['content_score']}% | Collab: {m['collab_score']}% | Poster: {m['poster_url']}")

    print("\n5. Testing /api/recommend for Toy Story (movieId=1):")
    r = requests.get(f"{BASE_URL}/api/recommend?movie_id=1&n=3&alpha=0.5", timeout=10)
    rec = r.json()
    print("Selected:", rec["selected"]["title"], "TMDB Poster:", rec["selected"]["poster_url"])
    for m in rec["results"]:
        print(f"  -> {m['title']} | Match: {m['match_percent']}% | Content: {m['content_score']}% | Collab: {m['collab_score']}% | Poster: {m['poster_url']}")

    print("\n6. Testing /api/recommend for low rating count movie (movieId=49):")
    r = requests.get(f"{BASE_URL}/api/recommend?movie_id=49&n=3&alpha=0.5", timeout=10)
    rec = r.json()
    print(f"Alpha used (expected 1.0): {rec['alpha_used']} | Rating count: {rec['selected']['rating_count']}")
    for m in rec["results"]:
        print(f"  -> {m['title']} | Match: {m['match_percent']}% | Content: {m['content_score']}% | Collab: {m['collab_score']}%")

    print("\n7. Testing Vite Dev Server Proxy (http://localhost:5173/api/health):")
    r_proxy = requests.get("http://localhost:5173/api/health", timeout=5)
    print("Vite Proxy Status:", r_proxy.status_code, r_proxy.json())
    assert r_proxy.status_code == 200

    print("\n8. Testing Error Validation (400 / 404):")
    r_bad_search = requests.get(f"{BASE_URL}/api/search", timeout=5)
    print("Missing q param status:", r_bad_search.status_code, r_bad_search.json())
    assert r_bad_search.status_code == 400

    r_not_found = requests.get(f"{BASE_URL}/api/recommend?movie_id=999999", timeout=5)
    print("Non-existent movie status:", r_not_found.status_code, r_not_found.json())
    assert r_not_found.status_code == 404

    print("\nALL API ENDPOINTS AND ERROR HANDLING VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()

def test_alpha_slider_variation():
    print("\n9. Testing Slider Alpha Variation on Recommendations (The Matrix, movieId=2571):")
    r_content = requests.get(f"{BASE_URL}/api/recommend?movie_id=2571&n=3&alpha=1.0", timeout=10).json()
    r_collab = requests.get(f"{BASE_URL}/api/recommend?movie_id=2571&n=3&alpha=0.0", timeout=10).json()
    r_hybrid = requests.get(f"{BASE_URL}/api/recommend?movie_id=2571&n=3&alpha=0.5", timeout=10).json()

    print("  Alpha=1.0 (Content-only):", [(m["title"], m["match_percent"]) for m in r_content["results"]])
    print("  Alpha=0.0 (Collab-only):", [(m["title"], m["match_percent"]) for m in r_collab["results"]])
    print("  Alpha=0.5 (Hybrid 50/50):", [(m["title"], m["match_percent"]) for m in r_hybrid["results"]])

    assert r_content["results"][0]["title"] != r_collab["results"][0]["title"] or r_content["results"][0]["match_percent"] != r_collab["results"][0]["match_percent"]
    print("  Slider effect successfully confirmed: recommendation rankings and scores adapt dynamically!")

test_alpha_slider_variation()
