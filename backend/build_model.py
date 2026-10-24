import os
import re
import pickle
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, save_npz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

try:
    from backend.download_data import ensure_dataset
except ImportError:
    from download_data import ensure_dataset

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
MODEL_DIR = os.path.join(BACKEND_DIR, "model")


def parse_title_year(raw_title: str):
    raw = str(raw_title).strip()
    match = re.search(r'\s*\((\d{4})\)\s*$', raw)
    if match:
        year = int(match.group(1))
        clean_title = re.sub(r'\s*\(\d{4}\)\s*$', '', raw).strip()
        return clean_title, year
    match_any = re.search(r'\((\d{4})\)', raw)
    if match_any:
        year = int(match_any.group(1))
        clean_title = re.sub(r'\((\d{4})\)', '', raw).strip()
        return clean_title, year
    return raw, None


def clean_genres(genres_str: str):
    if pd.isna(genres_str) or not genres_str or genres_str == "(no genres listed)":
        return []
    return [g.strip() for g in genres_str.split("|") if g.strip()]


def build_and_save_model():
    print("=" * 60)
    print("Precomputing CineMatch Recommender Artifacts...")
    print("=" * 60)

    ensure_dataset()
    os.makedirs(MODEL_DIR, exist_ok=True)

    movies_path = os.path.join(DATA_DIR, "movies.csv")
    ratings_path = os.path.join(DATA_DIR, "ratings.csv")
    links_path = os.path.join(DATA_DIR, "links.csv")

    print("[1/5] Loading MovieLens datasets...")
    movies = pd.read_csv(movies_path)
    ratings = pd.read_csv(ratings_path)
    links = pd.read_csv(links_path)

    # Clean and merge links
    links_clean = links[["movieId", "tmdbId"]].drop_duplicates("movieId")
    movies = movies.merge(links_clean, on="movieId", how="left")

    # Title, year, and genre parsing
    parsed = movies["title"].apply(parse_title_year)
    movies["clean_title"] = [p[0] for p in parsed]
    movies["year"] = [p[1] for p in parsed]
    movies["genre_list"] = movies["genres"].apply(clean_genres)

    # Compute rating counts and means per movie
    rating_stats = ratings.groupby("movieId").agg(
        rating_count=("rating", "count"),
        rating_mean=("rating", "mean")
    ).reset_index()

    movies = movies.merge(rating_stats, on="movieId", how="left")
    movies["rating_count"] = movies["rating_count"].fillna(0).astype(int)
    movies["rating_mean"] = movies["rating_mean"].fillna(0.0)
    movies = movies.reset_index(drop=True)

    n_movies = len(movies)
    movie_id_to_idx = {mid: idx for idx, mid in enumerate(movies["movieId"])}

    # Compute Bayesian weighted ratings
    m = 50
    C = float(ratings["rating"].mean()) if len(ratings) > 0 else 3.5
    v = movies["rating_count"].values
    R = movies["rating_mean"].values
    wr = (v / (v + m)) * R + (m / (v + m)) * C
    movies["weighted_rating"] = wr

    # [2/5] Build TF-IDF Content Model
    print("[2/5] Building TF-IDF Content Matrix...")
    soups = []
    for _, row in movies.iterrows():
        genres_clean = " ".join(row["genre_list"])
        title_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', row["clean_title"]).lower()
        soup = f"{genres_clean} {title_clean}".strip()
        soups.append(soup)

    tfidf_vectorizer = TfidfVectorizer(stop_words="english", token_pattern=r'(?u)\b\w+\b')
    tfidf_matrix = tfidf_vectorizer.fit_transform(soups)

    # [3/5] Build Collaborative TruncatedSVD Item Embeddings
    print("[3/5] Training Collaborative SVD Embeddings (float32)...")
    valid_ratings = ratings[ratings["movieId"].isin(movie_id_to_idx)].copy()
    user_means = valid_ratings.groupby("userId")["rating"].transform("mean")
    valid_ratings["centered_rating"] = valid_ratings["rating"] - user_means

    user_ids = valid_ratings["userId"].unique()
    user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
    n_users = len(user_ids)

    row_indices = valid_ratings["movieId"].map(movie_id_to_idx).values
    col_indices = valid_ratings["userId"].map(user_to_idx).values
    data_values = valid_ratings["centered_rating"].values

    item_user_matrix = csr_matrix(
        (data_values, (row_indices, col_indices)),
        shape=(n_movies, n_users),
        dtype=np.float32
    )

    svd = TruncatedSVD(n_components=50, random_state=42)
    item_embeddings = svd.fit_transform(item_user_matrix).astype(np.float32)

    norms = np.linalg.norm(item_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    item_embeddings_norm = (item_embeddings / norms).astype(np.float32)

    # [4/5] Precompute Popular Candidates
    print("[4/5] Calculating Bayesian Popular Ranking...")
    popular_df = movies[movies["rating_count"] >= 50].sort_values(
        by="weighted_rating", ascending=False
    ).reset_index(drop=True)

    # [5/5] Save all artifacts to backend/model/
    print(f"[5/5] Saving precomputed artifacts into {MODEL_DIR}...")
    save_npz(os.path.join(MODEL_DIR, "tfidf_matrix.npz"), tfidf_matrix)
    np.save(os.path.join(MODEL_DIR, "item_embeddings.npy"), item_embeddings_norm)
    np.save(os.path.join(MODEL_DIR, "rating_counts.npy"), movies["rating_count"].values.astype(np.int32))

    # Save lightweight metadata
    metadata_cols = [
        "movieId", "title", "clean_title", "year", "genres",
        "genre_list", "tmdbId", "rating_count", "rating_mean", "weighted_rating"
    ]
    movies_meta = movies[metadata_cols].copy()
    with open(os.path.join(MODEL_DIR, "movies_metadata.pkl"), "wb") as f:
        pickle.dump(movies_meta, f, protocol=pickle.HIGHEST_PROTOCOL)

    with open(os.path.join(MODEL_DIR, "popular_movies.pkl"), "wb") as f:
        pickle.dump(popular_df[metadata_cols], f, protocol=pickle.HIGHEST_PROTOCOL)

    print("\nPrecomputation complete!")
    print(f"Artifacts saved: tfidf_matrix.npz, item_embeddings.npy, rating_counts.npy, movies_metadata.pkl, popular_movies.pkl")
    print("=" * 60)


if __name__ == "__main__":
    build_and_save_model()
