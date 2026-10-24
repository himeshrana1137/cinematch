import os
import re
import pickle
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, load_npz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.decomposition import TruncatedSVD
from typing import List, Dict, Any, Optional

try:
    from backend.download_data import ensure_dataset
except ImportError:
    from download_data import ensure_dataset


class MovieRecommender:
    def __init__(self, data_dir: Optional[str] = None, model_dir: Optional[str] = None):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        else:
            self.data_dir = data_dir

        if model_dir is None:
            self.model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
        else:
            self.model_dir = model_dir

        self.movies_df: pd.DataFrame = pd.DataFrame()
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        
        # Content-based structures
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None

        # Collaborative structures
        self.item_embeddings = None
        self.item_embeddings_norm = None
        self.rating_counts = np.array([])

        # Precomputed popular list
        self.popular_movies_df: pd.DataFrame = pd.DataFrame()

        self._initialize()

    def _parse_title_year(self, raw_title: str):
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

    def _clean_genres(self, genres_str: str) -> List[str]:
        if pd.isna(genres_str) or not genres_str or genres_str == "(no genres listed)":
            return []
        return [g.strip() for g in genres_str.split("|") if g.strip()]

    def _initialize(self):
        # 1. Try loading precomputed model artifacts first (Fast startup, low RAM)
        if self._load_precomputed_model():
            return

        # 2. Fallback: Build from scratch if precomputed model is absent
        self._build_model_from_scratch()

    def _load_precomputed_model(self) -> bool:
        required_artifacts = [
            "tfidf_matrix.npz",
            "item_embeddings.npy",
            "rating_counts.npy",
            "movies_metadata.pkl",
            "popular_movies.pkl"
        ]
        all_present = all(
            os.path.exists(os.path.join(self.model_dir, f)) for f in required_artifacts
        )
        if not all_present:
            return False

        try:
            print("Loading precomputed CineMatch model artifacts from backend/model/...")
            with open(os.path.join(self.model_dir, "movies_metadata.pkl"), "rb") as f:
                self.movies_df = pickle.load(f)

            with open(os.path.join(self.model_dir, "popular_movies.pkl"), "rb") as f:
                self.popular_movies_df = pickle.load(f)

            self.tfidf_matrix = load_npz(os.path.join(self.model_dir, "tfidf_matrix.npz"))
            self.item_embeddings_norm = np.load(os.path.join(self.model_dir, "item_embeddings.npy"))
            self.rating_counts = np.load(os.path.join(self.model_dir, "rating_counts.npy"))

            self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(self.movies_df["movieId"])}
            self.idx_to_movie_id = {idx: mid for idx, mid in enumerate(self.movies_df["movieId"])}
            print(f"Precomputed model loaded: {len(self.movies_df)} titles ready!")
            return True
        except Exception as e:
            print(f"Warning: Failed to load precomputed model: {e}. Falling back to building from scratch...")
            return False

    def _build_model_from_scratch(self):
        print("Building recommender model from scratch...")
        ensure_dataset()

        movies_path = os.path.join(self.data_dir, "movies.csv")
        ratings_path = os.path.join(self.data_dir, "ratings.csv")
        links_path = os.path.join(self.data_dir, "links.csv")

        print("Loading MovieLens dataset...")
        movies = pd.read_csv(movies_path)
        ratings = pd.read_csv(ratings_path)
        links = pd.read_csv(links_path)

        # Merge links to map movieId -> tmdbId
        links_clean = links[["movieId", "tmdbId"]].drop_duplicates("movieId")
        movies = movies.merge(links_clean, on="movieId", how="left")

        # Parse title and year
        parsed = movies["title"].apply(self._parse_title_year)
        movies["clean_title"] = [p[0] for p in parsed]
        movies["year"] = [p[1] for p in parsed]
        movies["genre_list"] = movies["genres"].apply(self._clean_genres)

        # Calculate rating counts and means per movie
        rating_stats = ratings.groupby("movieId").agg(
            rating_count=("rating", "count"),
            rating_mean=("rating", "mean")
        ).reset_index()

        movies = movies.merge(rating_stats, on="movieId", how="left")
        movies["rating_count"] = movies["rating_count"].fillna(0).astype(int)
        movies["rating_mean"] = movies["rating_mean"].fillna(0.0)

        movies = movies.reset_index(drop=True)
        self.movies_df = movies
        n_movies = len(self.movies_df)

        self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(movies["movieId"])}
        self.idx_to_movie_id = {idx: mid for idx, mid in enumerate(movies["movieId"])}
        self.rating_counts = movies["rating_count"].values

        # TF-IDF on genres + clean title words
        soups = []
        for _, row in movies.iterrows():
            genres_clean = " ".join(row["genre_list"])
            title_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', row["clean_title"]).lower()
            soup = f"{genres_clean} {title_clean}".strip()
            soups.append(soup)

        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english", token_pattern=r'(?u)\b\w+\b')
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(soups)

        # Collaborative: SVD item embeddings
        valid_ratings = ratings[ratings["movieId"].isin(self.movie_id_to_idx)].copy()
        user_means = valid_ratings.groupby("userId")["rating"].transform("mean")
        valid_ratings["centered_rating"] = valid_ratings["rating"] - user_means

        user_ids = valid_ratings["userId"].unique()
        user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
        n_users = len(user_ids)

        row_indices = valid_ratings["movieId"].map(self.movie_id_to_idx).values
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
        self.item_embeddings_norm = (item_embeddings / norms).astype(np.float32)

        # Bayesian weighted ratings
        m = 50
        C = float(ratings["rating"].mean()) if len(ratings) > 0 else 3.5
        v = movies["rating_count"].values
        R = movies["rating_mean"].values

        wr = (v / (v + m)) * R + (m / (v + m)) * C
        self.movies_df["weighted_rating"] = wr

        popular_subset = self.movies_df[self.movies_df["rating_count"] >= 50].sort_values(
            by="weighted_rating", ascending=False
        )
        self.popular_movies_df = popular_subset.reset_index(drop=True)
        print(f"Recommender ready with {n_movies} movies and {len(self.popular_movies_df)} popular candidates.")

    def _row_to_card(self, row: pd.Series, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tmdb_id = row.get("tmdbId")
        if pd.isna(tmdb_id):
            tmdb_val = None
        else:
            try:
                tmdb_val = int(tmdb_id)
            except Exception:
                tmdb_val = None

        card = {
            "movieId": int(row["movieId"]),
            "title": str(row["clean_title"]),
            "full_title": str(row["title"]),
            "year": int(row["year"]) if pd.notna(row["year"]) else None,
            "genres": list(row["genre_list"]) if isinstance(row["genre_list"], list) else [],
            "tmdbId": tmdb_val,
            "rating_count": int(row.get("rating_count", 0)),
            "rating_mean": round(float(row.get("rating_mean", 0.0)), 1)
        }
        if extra:
            card.update(extra)
        return card

    def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        idx = self.movie_id_to_idx.get(movie_id)
        if idx is None:
            return None
        return self._row_to_card(self.movies_df.iloc[idx])

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []
        q = query.strip().lower()

        mask = (
            self.movies_df["title"].str.lower().str.contains(q, regex=False) |
            self.movies_df["clean_title"].str.lower().str.contains(q, regex=False)
        )
        matches = self.movies_df[mask].sort_values(by="rating_count", ascending=False).head(limit)

        results = []
        for _, row in matches.iterrows():
            results.append({
                "movieId": int(row["movieId"]),
                "title": str(row["clean_title"]),
                "full_title": str(row["title"]),
                "year": int(row["year"]) if pd.notna(row["year"]) else None,
                "rating_count": int(row["rating_count"]),
                "genres": list(row["genre_list"])
            })
        return results

    def popular(self, n: int = 12) -> List[Dict[str, Any]]:
        top_df = self.popular_movies_df.head(n)
        return [self._row_to_card(row) for _, row in top_df.iterrows()]

    def recommend(self, movie_id: int, n: int = 10, alpha: float = 0.5) -> Dict[str, Any]:
        idx = self.movie_id_to_idx.get(movie_id)
        if idx is None:
            raise ValueError(f"Movie ID {movie_id} not found in database.")

        selected_row = self.movies_df.iloc[idx]
        selected_card = self._row_to_card(selected_row)
        n_movies = len(self.movies_df)

        alpha = max(0.0, min(1.0, float(alpha)))

        # 1. Content-based similarity on demand using linear_kernel
        content_sim = linear_kernel(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()

        c_min, c_max = content_sim.min(), content_sim.max()
        if c_max > c_min:
            norm_content = (content_sim - c_min) / (c_max - c_min)
        else:
            norm_content = np.zeros(n_movies, dtype=np.float32)

        # 2. Collaborative similarity on demand
        selected_ratings_count = self.rating_counts[idx]
        is_collab_reliable = selected_ratings_count >= 5

        if is_collab_reliable:
            collab_sim = np.dot(self.item_embeddings_norm, self.item_embeddings_norm[idx])
            reliable_mask = self.rating_counts >= 5
            
            if np.any(reliable_mask):
                k_min = collab_sim[reliable_mask].min()
                k_max = collab_sim[reliable_mask].max()
                if k_max > k_min:
                    norm_collab = np.zeros(n_movies, dtype=np.float32)
                    norm_collab[reliable_mask] = (collab_sim[reliable_mask] - k_min) / (k_max - k_min)
                else:
                    norm_collab = np.zeros(n_movies, dtype=np.float32)
            else:
                norm_collab = np.zeros(n_movies, dtype=np.float32)
        else:
            alpha = 1.0
            norm_collab = np.zeros(n_movies, dtype=np.float32)

        # 3. Hybrid score combination
        final_scores = alpha * norm_content + (1.0 - alpha) * norm_collab
        final_scores[idx] = -1.0

        top_indices = np.argsort(final_scores)[::-1][:n]

        results = []
        for rec_idx in top_indices:
            row = self.movies_df.iloc[rec_idx]
            final_val = float(final_scores[rec_idx])
            c_val = float(norm_content[rec_idx])
            k_val = float(norm_collab[rec_idx])

            match_percent = round(max(0.0, min(100.0, final_val * 100.0)), 1)
            content_percent = round(max(0.0, min(100.0, c_val * 100.0)), 1)
            collab_percent = round(max(0.0, min(100.0, k_val * 100.0)), 1)

            results.append(self._row_to_card(row, {
                "match_percent": match_percent,
                "content_score": content_percent,
                "collab_score": collab_percent
            }))

        return {
            "selected": selected_card,
            "alpha_used": alpha,
            "results": results
        }
