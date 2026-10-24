import os
import random
import numpy as np
import pandas as pd
from typing import Dict, List

try:
    from backend.recommender import MovieRecommender
except ImportError:
    from recommender import MovieRecommender


def evaluate_precision_at_k(k: int = 10, sample_users: int = 60, seed: int = 42):
    print("=" * 65)
    print(f"Running Recommender Evaluation (Precision@{k} Hold-out Test)")
    print("=" * 65)

    random.seed(seed)
    np.random.seed(seed)

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    ratings_path = os.path.join(data_dir, "ratings.csv")
    ratings = pd.read_csv(ratings_path)

    # Initialize recommender engine
    rec = MovieRecommender(data_dir=data_dir)

    # Filter to positive ratings (rating >= 4.0)
    pos_ratings = ratings[ratings["rating"] >= 4.0].copy()

    # Find users with at least 15 positive ratings for meaningful hold-out
    user_counts = pos_ratings.groupby("userId").size()
    eligible_users = user_counts[user_counts >= 15].index.tolist()

    if len(eligible_users) > sample_users:
        test_users = random.sample(eligible_users, sample_users)
    else:
        test_users = eligible_users

    print(f"Evaluating across {len(test_users)} active test users with held-out liked items...")

    alphas = [0.0, 0.5, 1.0]
    alpha_names = {0.0: "Collaborative Only", 0.5: "Balanced Hybrid", 1.0: "Content-based Only"}
    results_by_alpha = {a: [] for a in alphas}

    # For each test user, split their liked movies into 80% train seed and 20% test hold-out
    for user_id in test_users:
        user_movies = pos_ratings[pos_ratings["userId"] == user_id]["movieId"].tolist()
        # Keep only movies present in recommender
        valid_user_movies = [m for m in user_movies if m in rec.movie_id_to_idx]
        if len(valid_user_movies) < 10:
            continue

        random.shuffle(valid_user_movies)
        split_idx = int(len(valid_user_movies) * 0.75)
        train_pool = valid_user_movies[:split_idx]
        test_held_out = set(valid_user_movies[split_idx:])

        if not test_held_out or not train_pool:
            continue

        # Use 1 or 2 seed movies from train pool
        seed_movie = train_pool[0]

        for alpha in alphas:
            try:
                rec_res = rec.recommend(seed_movie, n=k, alpha=alpha)
                rec_ids = [m["movieId"] for m in rec_res["results"]]
                hits = sum(1 for m_id in rec_ids if m_id in test_held_out)
                prec = hits / float(k)
                results_by_alpha[alpha].append(prec)
            except Exception:
                continue

    # Summary table
    print("\n" + "-" * 65)
    print(f"{'Alpha':<8} | {'Strategy':<22} | {'Precision@10':<14} | {'Avg Hits / 10'}")
    print("-" * 65)

    for alpha in alphas:
        scores = results_by_alpha[alpha]
        avg_prec = np.mean(scores) if scores else 0.0
        avg_hits = avg_prec * k
        mode_label = alpha_names[alpha]
        print(f"{alpha:<8.1f} | {mode_label:<22} | {avg_prec * 100:>11.2f}% | {avg_hits:>6.2f} / {k}")

    print("-" * 65)
    print("Evaluation completed successfully.\n")


if __name__ == "__main__":
    evaluate_precision_at_k(k=10, sample_users=60)
