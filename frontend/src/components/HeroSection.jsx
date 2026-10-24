import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Sparkles, Star, Clock, Info } from 'lucide-react';
import { formatTitle, formatRuntime } from '../utils/format';

export default function HeroSection({
  movie,
  onWatchTrailer,
  onMoreLikeThis,
  onOpenDetails
}) {
  if (!movie) return null;

  const {
    title,
    year,
    genres = [],
    backdrop_url,
    overview,
    tagline,
    runtime,
    tmdb_rating,
    match_percent
  } = movie;

  const displayTitle = formatTitle(title);

  return (
    <div className="cinema-hero">
      {/* Background with crossfade transition */}
      <div className="hero-backdrop-container">
        <AnimatePresence mode="wait">
          <motion.div
            key={backdrop_url || title}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
            style={{ width: '100%', height: '100%', position: 'absolute', inset: 0 }}
          >
            {backdrop_url ? (
              <img
                src={backdrop_url}
                alt={displayTitle}
                className="hero-backdrop-img"
              />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background: 'radial-gradient(circle at 60% 30%, #1f1f33 0%, #0a0a0f 75%)'
                }}
              />
            )}
          </motion.div>
        </AnimatePresence>
        <div className="hero-gradient-left" />
        <div className="hero-gradient-bottom" />
      </div>

      {/* Content wrapper */}
      <div className="hero-content-wrap">
        {match_percent !== undefined && match_percent !== null && (
          <div className="hero-meta-badge">
            <Sparkles size={14} />
            <span>{Math.round(match_percent)}% Match for You</span>
          </div>
        )}

        <h1 className="hero-title">{displayTitle}</h1>

        {tagline && <p className="hero-tagline">"{tagline}"</p>}

        <div className="hero-stats-row">
          {tmdb_rating ? (
            <span className="hero-rating-badge">
              <Star size={15} fill="currentColor" /> {tmdb_rating} TMDB
            </span>
          ) : null}

          {year && <span>{year}</span>}

          {runtime ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              <Clock size={14} /> {formatRuntime(runtime)}
            </span>
          ) : null}

          {genres && genres.length > 0 && (
            <div className="hero-genres-row">
              {genres.slice(0, 3).map((g) => (
                <span key={g} className="hero-genre-chip">
                  {g}
                </span>
              ))}
            </div>
          )}
        </div>

        {overview && <p className="hero-overview">{overview}</p>}

        <div className="hero-buttons-row">
          <button
            className="btn-primary-gradient"
            onClick={() => onWatchTrailer && onWatchTrailer(movie)}
          >
            <Play size={18} fill="currentColor" />
            <span>Watch Trailer</span>
          </button>

          <button
            className="btn-secondary-glass"
            onClick={() => onMoreLikeThis && onMoreLikeThis(movie)}
          >
            <Sparkles size={18} />
            <span>More Like This</span>
          </button>

          <button
            className="btn-secondary-glass"
            onClick={() => onOpenDetails && onOpenDetails(movie)}
            title="Full Details & Cast"
          >
            <Info size={18} />
            <span>Details</span>
          </button>
        </div>
      </div>
    </div>
  );
}
