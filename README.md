# CineMatch: Hybrid Movie Recommendation Engine 🎬

A complete, lightweight, end-to-end hybrid movie recommendation web application built with **Flask**, **Scikit-learn**, and **React (Vite)** using the **MovieLens 100k** dataset and the **TMDB (The Movie Database)** API.

Designed specifically to run efficiently on Windows laptops (8 GB RAM) without requiring heavy dependencies or C++ build tools.

---

## 🌟 Features

- **Hybrid Recommendation Algorithm**: Combines **Content-Based Filtering** (TF-IDF on genres and title keywords) and **Collaborative Filtering** (User-item matrix mean-centering + TruncatedSVD embeddings).
- **Interactive Weight Tuning**: Real-time slider mapping $\alpha \in [0.0, 1.0]$ allowing users to balance content similarity versus collaborative rating patterns.
- **Cold-Start / Sparsity Protection**: Automatically detects low-review items ($< 5$ ratings) and falls back to pure content-based filtering ($\alpha = 1.0$).
- **TMDB Enrichment & Multi-threaded Caching**: Fetches high-resolution posters, movie overviews, release years, and community vote averages in parallel (`ThreadPoolExecutor`), caching results to `backend/data/tmdb_cache.json`.
- **Autocomplete Search**: Debounced instant search dropdown matching titles, years, genres, and community review counts.
- **Bayesian Weighted Popularity**: Home page showcases top-ranked movies using IMDb-style Bayesian average weighting with a minimum 50 ratings threshold.
- **Modern Responsive Dark UI**: Built with React and plain CSS (no heavy UI frameworks) featuring loading skeletons, badges, and responsive design.

---

## 🏗️ Architecture & Project Structure

```
movie-recommender/
│
├── backend/
│   ├── data/                 # MovieLens dataset & TMDB cache
│   │   ├── movies.csv
│   │   ├── ratings.csv
│   │   ├── links.csv
│   │   └── tmdb_cache.json
│   ├── .env                  # API keys (never committed)
│   ├── .env.example          # Template for environment variables
│   ├── requirements.txt      # Python dependencies
│   ├── download_data.py      # Dataset download and extraction utility
│   ├── recommender.py        # Hybrid recommendation engine
│   ├── tmdb.py               # TMDB client with ThreadPoolExecutor & caching
│   ├── app.py                # Flask REST API server (Port 5000)
│   ├── evaluate.py           # Precision@10 holdout evaluation script
│   └── test_api.py           # Automated test suite
│
├── frontend/                 # React 18 + Vite (Port 5173)
│   ├── src/
│   │   ├── components/
│   │   │   ├── MovieCard.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── SliderControl.jsx
│   │   │   ├── SelectedMovieHero.jsx
│   │   │   └── SkeletonGrid.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js       # Configured with proxy: /api -> http://localhost:5000
│
├── run.bat                   # 1-click startup script for Windows
├── .gitignore
└── README.md
```

---

## 🧠 How the Hybrid Scoring Works

The engine computes similarity for any selected movie $i$ across all candidates $j$:

### 1. Content-Based Similarity
- For each movie, a text feature string is constructed:
  $$\text{Soup} = \text{Cleaned Genres (space separated)} + \text{Cleaned Title Words}$$
- A `TfidfVectorizer` (with English stop words removed) converts the text into TF-IDF representations.
- To prevent memory exhaustion on 8 GB RAM machines, **no full $N \times N$ matrix is stored in memory**.
- Cosine similarity is computed **on demand** using `linear_kernel(tfidf[i], tfidf)`:
  $$S_{\text{content}}(i, j) = \text{CosineSimilarity}(\vec{t}_i, \vec{t}_j)$$
- Scores are Min-Max normalized to the range $[0, 1]$:
  $$\hat{S}_{\text{content}}(j) = \frac{S_{\text{content}}(i, j) - \min(S_{\text{content}})}{\max(S_{\text{content}}) - \min(S_{\text{content}})}$$

### 2. Collaborative Filtering (Item Embeddings via TruncatedSVD)
- User ratings are **mean-centered per user** to remove user rating bias (optimistic vs. harsh raters):
  $$r'_{u, m} = r_{u, m} - \bar{r}_u$$
- A sparse item-user matrix $R \in \mathbb{R}^{N_{\text{movies}} \times N_{\text{users}}}$ is constructed.
- `TruncatedSVD(n_components=50, random_state=42)` decomposes the matrix to extract 50-dimensional latent item embeddings:
  $$E = \text{TruncatedSVD}(R) \in \mathbb{R}^{N_{\text{movies}} \times 50}$$
- Item embeddings are L2-normalized:
  $$\hat{E}_m = \frac{E_m}{\|E_m\|_2}$$
- On-demand collaborative similarity is computed as the dot product:
  $$S_{\text{collab}}(i, j) = \hat{E}_i \cdot \hat{E}_j$$
- Any movie with fewer than 5 ratings is considered unreliable and its collaborative score is set to 0.
- Scores for reliable items are Min-Max normalized to $[0, 1]$.

### 3. Hybrid Combination & Cold-Start Rule
- The final score is a weighted combination:
  $$\text{FinalScore}(j) = \alpha \cdot \hat{S}_{\text{content}}(j) + (1 - \alpha) \cdot \hat{S}_{\text{collab}}(j)$$
- **Cold-Start Fallback**: If the selected movie $i$ has $< 5$ ratings, collaborative similarity is unreliable; the engine automatically sets $\alpha = 1.0$ (content-only).
- The query movie $i$ is excluded ($\text{FinalScore}(i) = -1$).
- Recommendations are sorted descending, returning the top $N$ items with:
  - $\text{Match Percentage} = \text{round}(\text{FinalScore} \times 100, 1)$
  - Individual Content Score and Collaborative Score percentages.

### 4. Bayesian Weighted Rating (Popular Movies)
For the home page, movies with $\ge 50$ ratings are ranked by Bayesian average:
$$WR = \left(\frac{v}{v + m}\right) R + \left(\frac{m}{v + m}\right) C$$
where:
- $v$: Number of ratings for the movie
- $m$: Minimum rating threshold (50)
- $R$: Average rating for the movie
- $C$: Mean rating across all movies in the dataset

---

## 🚀 Quick Start (Windows)

### Option 1: One-Click Startup Script
Simply double-click `run.bat` or run:
```cmd
run.bat
```
`run.bat` automatically:
1. Creates the Python virtual environment (`venv`) if missing.
2. Installs backend dependencies from `backend/requirements.txt`.
3. Installs frontend packages in `frontend/` if missing.
4. Launches the Flask API (`http://localhost:5000`) and the Vite React app (`http://localhost:5173`) in two dedicated command windows.

---

### Option 2: Manual Step-by-Step Setup

#### 1. Setup Backend
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install requirements
pip install -r backend/requirements.txt

# Create .env file with your TMDB key
# TMDB_API_KEY=your_key_here

# Run dataset downloader (if not already downloaded)
python backend/download_data.py

# Start Flask server
python backend/app.py
```

#### 2. Setup Frontend
In another command prompt:
```cmd
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 📡 REST API Reference

The backend runs on `http://localhost:5000` (and is proxied via `/api` in Vite).

| Method | Endpoint | Description | Query Parameters | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Healthcheck | None | `{"status": "ok"}` |
| `GET` | `/api/search` | Case-insensitive title search | `q` (required, str) | `[{"movieId": 1, "title": "Toy Story", "year": 1995, ...}]` |
| `GET` | `/api/popular` | Bayesian top-rated movies | `n` (default 12, max 50) | Array of movie cards with posters, backdrops, cast & trailers |
| `GET` | `/api/movie/<id>` | Full movie detail card | Path param: `id` (int) | Comprehensive movie card with backdrop, runtime, tagline, cast & trailer |
| `GET` | `/api/recommend` | Hybrid recommendations | `movie_id` (required, int), `n` (default 10), `alpha` (default 0.5) | `{"selected": card, "alpha_used": float, "results": [cards]}` |

### Movie Card Schema
```json
{
  "movieId": 1,
  "title": "Toy Story",
  "year": 1995,
  "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"],
  "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
  "overview": "Led by Woody, Andy's toys live happily in his room...",
  "tmdb_rating": 8.0,
  "rating_count": 215,
  "match_percent": 85.7,
  "content_score": 92.9,
  "collab_score": 78.4
}
```

---

## 📊 Offline Evaluation (Bonus)

To evaluate precision@10 on a holdout test set:
```cmd
python backend/evaluate.py
```

### Evaluation Output Sample:
```text
=================================================================
Running Recommender Evaluation (Precision@10 Hold-out Test)
=================================================================
Alpha    | Strategy               | Precision@10   | Avg Hits / 10
-----------------------------------------------------------------
0.0      | Collaborative Only     |        3.50% |   0.35 / 10
0.5      | Balanced Hybrid        |        3.17% |   0.32 / 10
1.0      | Content-based Only     |        0.67% |   0.07 / 10
-----------------------------------------------------------------
Evaluation completed successfully.
```

---

## 🚀 Deploying to Render (Free Web Service)

This repository is optimized for deployment as a single web service on [Render](https://render.com) (Free 512 MB RAM / 0.1 CPU tier).

### Offline Model Precomputation
The repository includes precomputed model artifacts in `backend/model/` (TF-IDF matrices, normalized TruncatedSVD float32 item embeddings, and metadata). At runtime, the server loads these artifacts in $\approx 0.13$ seconds using only $\approx 165$ MB RAM (comfortably below Render's 512 MB threshold).

If you modify the training dataset, rebuild the model locally before committing:
```bash
python backend/build_model.py
```

### Deploying via GitHub & Render Blueprint

#### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Deploy CineMatch to Render"
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git branch -M main
git push -u origin main
```

#### Step 2: Deploy on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Blueprint** (or **Web Service**).
3. Connect your GitHub repository.
4. Render will automatically detect [`render.yaml`](file:///c:/Users/lenovo/Desktop/movie-recommender/render.yaml):
   - **Environment**: Python 3.11.9
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Plan**: Free
5. In the **Environment Variables** prompt on Render:
   - Enter your `TMDB_API_KEY`: `3baf522a793ab10d97b543e1d94e6005` (or your personal TMDB API key).
6. Click **Apply** / **Deploy**.

Render will install the requirements, start Gunicorn, and serve the built React UI and Flask API seamlessly from a single web service URL.

---

## ⚖️ Attribution & Disclaimer
This product uses the TMDB API but is not endorsed or certified by TMDB.
MovieLens dataset provided by GroupLens Research at the University of Minnesota.
