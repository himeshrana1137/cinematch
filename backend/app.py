import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment: local .env if available, otherwise rely on system environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

try:
    from backend.recommender import MovieRecommender
    from backend.tmdb import enrich_movie_cards
except ImportError:
    from recommender import MovieRecommender
    from tmdb import enrich_movie_cards

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Locate the frontend/dist folder
candidate_dist_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "dist")),
]

DIST_DIR = None
for p in candidate_dist_dirs:
    if os.path.exists(p) and os.path.isdir(p):
        DIST_DIR = p
        break

logger.info(f"Frontend static directory: {DIST_DIR}")

app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
CORS(app)

# Initialize recommender engine once at startup
logger.info("Initializing MovieRecommender engine...")
recommender = MovieRecommender()
logger.info("MovieRecommender engine ready!")


# API Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": getattr(error, "description", "Bad Request")}), 400


@app.errorhandler(404)
def not_found(error):
    # Only return JSON error if it is an API route
    if request.path.startswith("/api"):
        return jsonify({"error": getattr(error, "description", "Resource Not Found")}), 404
    # For SPA client routes, fallback to index.html
    if DIST_DIR and os.path.exists(DIST_DIR):
        index_file = os.path.join(DIST_DIR, "index.html")
        if os.path.exists(index_file):
            return send_from_directory(DIST_DIR, "index.html")
    return jsonify({"error": "Resource Not Found"}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal Server Error"}), 500


# ============================================================================
# API Routes (Keep all /api routes unchanged)
# ============================================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required and cannot be empty"}), 400

    results = recommender.search(query, limit=10)
    simplified = [
        {
            "movieId": r["movieId"],
            "title": r["title"],
            "full_title": r.get("full_title", r["title"]),
            "year": r["year"],
            "rating_count": r.get("rating_count", 0),
            "genres": r.get("genres", [])
        }
        for r in results
    ]
    return jsonify(simplified)


@app.route("/api/popular", methods=["GET"])
def popular():
    n_param = request.args.get("n", "12")
    try:
        n = int(n_param)
        n = max(1, min(50, n))
    except ValueError:
        return jsonify({"error": "Parameter 'n' must be an integer"}), 400

    raw_popular = recommender.popular(n=n)
    enriched = enrich_movie_cards(raw_popular)

    cards = []
    for m in enriched:
        cards.append({
            "movieId": m["movieId"],
            "title": m["title"],
            "year": m["year"],
            "genres": m["genres"],
            "poster_url": m.get("poster_url"),
            "backdrop_url": m.get("backdrop_url"),
            "overview": m.get("overview"),
            "tagline": m.get("tagline"),
            "runtime": m.get("runtime"),
            "tmdb_rating": m.get("tmdb_rating"),
            "rating_count": m.get("rating_count", 0),
            "rating_mean": m.get("rating_mean", 0.0),
            "cast": m.get("cast", []),
            "trailer_key": m.get("trailer_key")
        })
    return jsonify(cards)


@app.route("/api/movie/<movie_id>", methods=["GET"])
def get_movie_detail(movie_id):
    try:
        m_id = int(movie_id)
    except ValueError:
        return jsonify({"error": f"Invalid movie_id '{movie_id}', must be an integer"}), 400

    card = recommender.get_movie_by_id(m_id)
    if not card:
        return jsonify({"error": f"Movie ID {m_id} not found"}), 404

    enriched = enrich_movie_cards([card])
    res = enriched[0]

    return jsonify({
        "movieId": res["movieId"],
        "title": res["title"],
        "full_title": res.get("full_title", res["title"]),
        "year": res["year"],
        "genres": res["genres"],
        "poster_url": res.get("poster_url"),
        "backdrop_url": res.get("backdrop_url"),
        "overview": res.get("overview"),
        "tagline": res.get("tagline"),
        "runtime": res.get("runtime"),
        "tmdb_rating": res.get("tmdb_rating"),
        "rating_count": res.get("rating_count", 0),
        "rating_mean": res.get("rating_mean", 0.0),
        "cast": res.get("cast", []),
        "trailer_key": res.get("trailer_key")
    })


@app.route("/api/recommend", methods=["GET"])
def recommend():
    movie_id_param = request.args.get("movie_id")
    if not movie_id_param:
        return jsonify({"error": "Query parameter 'movie_id' is required"}), 400

    try:
        movie_id = int(movie_id_param)
    except ValueError:
        return jsonify({"error": "Query parameter 'movie_id' must be a valid integer"}), 400

    n_param = request.args.get("n", "10")
    try:
        n = int(n_param)
        n = max(1, min(50, n))
    except ValueError:
        return jsonify({"error": "Query parameter 'n' must be an integer"}), 400

    alpha_param = request.args.get("alpha", "0.5")
    try:
        alpha = float(alpha_param)
        alpha = max(0.0, min(1.0, alpha))
    except ValueError:
        return jsonify({"error": "Query parameter 'alpha' must be a float between 0.0 and 1.0"}), 400

    try:
        rec_data = recommender.recommend(movie_id=movie_id, n=n, alpha=alpha)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    # Enrich selected movie and recommendations in parallel
    enriched_selected_list = enrich_movie_cards([rec_data["selected"]])
    enriched_results_list = enrich_movie_cards(rec_data["results"])

    sel = enriched_selected_list[0]
    selected_card = {
        "movieId": sel["movieId"],
        "title": sel["title"],
        "year": sel["year"],
        "genres": sel["genres"],
        "poster_url": sel.get("poster_url"),
        "backdrop_url": sel.get("backdrop_url"),
        "overview": sel.get("overview"),
        "tagline": sel.get("tagline"),
        "runtime": sel.get("runtime"),
        "tmdb_rating": sel.get("tmdb_rating"),
        "rating_count": sel.get("rating_count", 0),
        "rating_mean": sel.get("rating_mean", 0.0),
        "cast": sel.get("cast", []),
        "trailer_key": sel.get("trailer_key")
    }

    results_cards = []
    for r in enriched_results_list:
        results_cards.append({
            "movieId": r["movieId"],
            "title": r["title"],
            "year": r["year"],
            "genres": r["genres"],
            "poster_url": r.get("poster_url"),
            "backdrop_url": r.get("backdrop_url"),
            "overview": r.get("overview"),
            "tagline": r.get("tagline"),
            "runtime": r.get("runtime"),
            "tmdb_rating": r.get("tmdb_rating"),
            "match_percent": r.get("match_percent"),
            "content_score": r.get("content_score"),
            "collab_score": r.get("collab_score"),
            "rating_count": r.get("rating_count", 0),
            "cast": r.get("cast", []),
            "trailer_key": r.get("trailer_key")
        })

    return jsonify({
        "selected": selected_card,
        "alpha_used": rec_data["alpha_used"],
        "results": results_cards
    })


# ============================================================================
# Static Files & SPA Fallback (Serve built React frontend)
# ============================================================================

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    # Never intercept API calls
    if path.startswith("api"):
        return jsonify({"error": f"API endpoint '/{path}' not found"}), 404

    # If static file exists in DIST_DIR, serve it
    if DIST_DIR and os.path.exists(DIST_DIR):
        file_path = os.path.join(DIST_DIR, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(DIST_DIR, path)
        # Fallback to index.html for client-side routing
        index_file = os.path.join(DIST_DIR, "index.html")
        if os.path.exists(index_file):
            return send_from_directory(DIST_DIR, "index.html")

    return jsonify({
        "status": "online",
        "message": "Flask API running. Frontend static build not found in frontend/dist. For local development, run Vite dev server at http://localhost:5173"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
