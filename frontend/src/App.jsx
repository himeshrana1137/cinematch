import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Film,
  SlidersHorizontal,
  Sparkles,
  Flame,
  Clapperboard,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';

import { formatTitle } from './utils/format';
import SearchBar from './components/SearchBar';
import HeroSection from './components/HeroSection';
import MovieRow from './components/MovieRow';
import DetailModal from './components/DetailModal';
import HybridControlPanel from './components/HybridControlPanel';
import SkeletonRow from './components/SkeletonRow';

export default function App() {
  const [popularMovies, setPopularMovies] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [modalMovie, setModalMovie] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [autoplayTrailer, setAutoplayTrailer] = useState(false);

  const [alpha, setAlpha] = useState(0.5);
  const [alphaUsed, setAlphaUsed] = useState(0.5);
  const [isLoadingPopular, setIsLoadingPopular] = useState(true);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [error, setError] = useState(null);

  const shouldReduceMotion = useReducedMotion();

  // Fetch popular movies on mount
  const fetchPopular = useCallback(async () => {
    setIsLoadingPopular(true);
    setError(null);
    try {
      // Fetch 24 popular titles to populate both Popular and Genre rows
      const res = await fetch('/api/popular?n=24');
      if (!res.ok) {
        throw new Error(`Failed to load popular titles (HTTP ${res.status})`);
      }
      const data = await res.json();
      setPopularMovies(data);
    } catch (err) {
      console.error('Error fetching popular movies:', err);
      setError('Backend service is not reachable. Ensure the Flask server is running on port 5000.');
    } finally {
      setIsLoadingPopular(false);
    }
  }, []);

  // Fetch recommendations for selected movie
  const fetchRecommendations = useCallback(async (movieId, currentAlpha) => {
    setIsLoadingRecs(true);
    setError(null);
    try {
      const res = await fetch(`/api/recommend?movie_id=${movieId}&n=12&alpha=${currentAlpha}`);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || `Failed to fetch recommendations (HTTP ${res.status})`);
      }
      const data = await res.json();
      setSelectedMovie(data.selected);
      setAlphaUsed(data.alpha_used ?? currentAlpha);
      setRecommendations(data.results || []);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err.message || 'Error loading recommendations from server.');
    } finally {
      setIsLoadingRecs(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchPopular();
  }, [fetchPopular]);

  // Current hero movie: either the selected movie or the top popular movie
  const heroMovie = selectedMovie || (popularMovies.length > 0 ? popularMovies[0] : null);

  // Third row: "More <top genre>" from hero movie's primary genre
  const topGenre = useMemo(() => {
    if (heroMovie && heroMovie.genres && heroMovie.genres.length > 0) {
      return heroMovie.genres[0];
    }
    return null;
  }, [heroMovie]);

  const genreMovies = useMemo(() => {
    if (!topGenre || popularMovies.length === 0) return [];
    // Filter popular movies by this genre (excluding current hero)
    return popularMovies.filter(
      (m) =>
        m.genres &&
        m.genres.includes(topGenre) &&
        (!heroMovie || m.movieId !== heroMovie.movieId)
    );
  }, [topGenre, popularMovies, heroMovie]);

  // Handle movie selection
  const handleSelectMovie = (movie) => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    fetchRecommendations(movie.movieId, alpha);
  };

  // Re-fetch recommendations when committing alpha slider
  const handleCommitAlpha = (newAlpha) => {
    if (selectedMovie) {
      fetchRecommendations(selectedMovie.movieId, newAlpha);
    }
  };

  // Open modal helpers
  const handleOpenDetails = (movie, playTrailer = false) => {
    setModalMovie(movie);
    setAutoplayTrailer(playTrailer);
    setIsModalOpen(true);
  };

  const handleWatchTrailerHero = (movie) => {
    handleOpenDetails(movie, true);
  };

  const handleMoreLikeThisHero = (movie) => {
    if (selectedMovie && selectedMovie.movieId === movie.movieId) {
      const el = document.getElementById('recommendations-row');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else {
      handleSelectMovie(movie);
    }
  };

  const scrollToTuning = () => {
    const el = document.getElementById('hybrid-controls');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const isContentOnlyFallback =
    selectedMovie &&
    selectedMovie.rating_count !== undefined &&
    selectedMovie.rating_count < 5;

  return (
    <motion.div
      className="app-viewport"
      initial={{ opacity: shouldReduceMotion ? 1 : 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Sticky Glass Navbar */}
      <header className="cinema-navbar">
        <div className="navbar-container">
          <div
            className="brand-wrapper"
            onClick={() => {
              setSelectedMovie(null);
              setRecommendations([]);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            title="CineMatch Home"
          >
            <div className="brand-icon-box">
              <Film size={20} />
            </div>
            <div>
              <span className="brand-heading">CineMatch</span>
            </div>
            <span className="brand-badge">PRO</span>
          </div>

          <SearchBar onSelectMovie={handleSelectMovie} />

          <div className="nav-actions">
            <button
              className="nav-pill-btn"
              onClick={scrollToTuning}
              title="Tune hybrid algorithm weights"
            >
              <SlidersHorizontal size={15} />
              <span>Weights ({Math.round(alpha * 100)}/{Math.round((1 - alpha) * 100)})</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {heroMovie && (
        <HeroSection
          movie={heroMovie}
          onWatchTrailer={handleWatchTrailerHero}
          onMoreLikeThis={handleMoreLikeThisHero}
          onOpenDetails={handleOpenDetails}
        />
      )}

      {/* Main Content Area */}
      <main className="cinema-main">
        {/* Error Banner */}
        {error && (
          <div className="error-banner-cinema">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <AlertTriangle size={20} />
              <div>
                <strong>Connection Error:</strong> {error}
              </div>
            </div>
            <button
              className="error-banner-btn"
              onClick={() => {
                if (selectedMovie) {
                  fetchRecommendations(selectedMovie.movieId, alpha);
                } else {
                  fetchPopular();
                }
              }}
            >
              <RotateCcw size={14} style={{ display: 'inline', marginRight: '4px' }} />
              Retry
            </button>
          </div>
        )}

        {/* Row 1: Recommendations (Because you picked ...) */}
        <div id="recommendations-row">
          {isLoadingRecs ? (
            <SkeletonRow
              title={
                selectedMovie
                  ? `Curating titles similar to ${formatTitle(selectedMovie.title)}...`
                  : 'Analyzing movie features...'
              }
            />
          ) : (
            selectedMovie && (
              <MovieRow
                title={`Because you picked ${formatTitle(selectedMovie.title)}`}
                subtitle="Ranked by live hybrid score combining storyline themes and viewer taste patterns"
                movies={recommendations}
                onSelectMovie={handleSelectMovie}
                onOpenDetails={handleOpenDetails}
                icon={Sparkles}
              />
            )
          )}
        </div>

        {/* Row 2: Popular Right Now */}
        {isLoadingPopular ? (
          <SkeletonRow title="Loading popular movies..." />
        ) : (
          <MovieRow
            title="Popular Right Now"
            subtitle="Top-rated cinematic releases calculated via Bayesian weighted rating"
            movies={popularMovies.slice(0, 12)}
            onSelectMovie={handleSelectMovie}
            onOpenDetails={handleOpenDetails}
            icon={Flame}
          />
        )}

        {/* Row 3: More in <Top Genre> */}
        {genreMovies.length > 0 && (
          <MovieRow
            title={`More in ${topGenre}`}
            subtitle={`Explore critically acclaimed ${topGenre} films`}
            movies={genreMovies}
            onSelectMovie={handleSelectMovie}
            onOpenDetails={handleOpenDetails}
            icon={Clapperboard}
          />
        )}

        {/* Hybrid Algorithm Control Panel */}
        <HybridControlPanel
          alpha={alpha}
          onChangeAlpha={setAlpha}
          onCommitAlpha={handleCommitAlpha}
          disabled={isLoadingRecs}
          isContentOnlyFallback={isContentOnlyFallback}
        />
      </main>

      {/* Detail Modal */}
      <DetailModal
        movie={modalMovie}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onFindSimilar={handleSelectMovie}
        initialPlayTrailer={autoplayTrailer}
      />

      {/* Cinematic Minimal Footer */}
      <footer className="cinema-footer">
        <div className="footer-content">
          <p className="tmdb-attribution-text">
            This product uses the TMDB API but is not endorsed or certified by TMDB.
          </p>
          <p className="footer-copyright">
            CineMatch Recommendation Engine • Powered by MovieLens 100k, Scikit-learn (TF-IDF &amp; TruncatedSVD), and React (Vite).
          </p>
        </div>
      </footer>
    </motion.div>
  );
}
