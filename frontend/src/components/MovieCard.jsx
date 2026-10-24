import React, { useState } from 'react';
import { Star, Info, Film } from 'lucide-react';
import { formatTitle } from '../utils/format';

export default function MovieCard({
  movie,
  onSelect,
  onOpenDetails,
  isSelected = false
}) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);

  const {
    title,
    year,
    genres = [],
    poster_url,
    tmdb_rating,
    match_percent
  } = movie;

  const displayTitle = formatTitle(title);
  const hasPoster = Boolean(poster_url && !imgError);

  // SVG Progress Ring calculations
  const ringRadius = 15;
  const circumference = 2 * Math.PI * ringRadius;
  const strokeDashoffset = match_percent !== undefined && match_percent !== null
    ? circumference - (Math.min(100, Math.max(0, match_percent)) / 100) * circumference
    : circumference;

  return (
    <div
      className={`cinema-movie-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect && onSelect(movie)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect && onSelect(movie);
        }
      }}
      title={`Click to view recommendations for ${displayTitle}`}
    >
      <div className="card-aspect-box">
        {/* Shimmer loading placeholder */}
        {!imgLoaded && !imgError && <div className="card-shimmer" />}

        {hasPoster ? (
          <img
            src={poster_url}
            alt={displayTitle}
            className="card-poster"
            loading="lazy"
            onLoad={() => setImgLoaded(true)}
            onError={() => {
              setImgLoaded(true);
              setImgError(true);
            }}
          />
        ) : (
          <div className="card-fallback-box">
            <Film size={32} />
            <div className="fallback-title">{displayTitle}</div>
            {year && <div style={{ fontSize: '0.75rem', marginTop: '0.2rem' }}>({year})</div>}
          </div>
        )}

        {/* Circular SVG Match Ring (For recommendations) */}
        {match_percent !== undefined && match_percent !== null && (
          <div className="match-ring-badge" title={`Match Score: ${match_percent}%`}>
            <svg className="match-ring-svg" viewBox="0 0 36 36">
              <defs>
                <linearGradient id={`matchGrad-${movie.movieId}`} x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#7c5cff" />
                  <stop offset="100%" stopColor="#f5b942" />
                </linearGradient>
              </defs>
              <circle
                className="match-ring-bg"
                cx="18"
                cy="18"
                r={ringRadius}
                strokeWidth="3"
              />
              <circle
                className="match-ring-progress"
                cx="18"
                cy="18"
                r={ringRadius}
                strokeWidth="3"
                stroke={`url(#matchGrad-${movie.movieId})`}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
              />
            </svg>
            <span className="match-ring-text">{Math.round(match_percent)}%</span>
          </div>
        )}

        {/* Info button to open detail modal */}
        <button
          className="card-info-btn"
          aria-label={`View details for ${displayTitle}`}
          onClick={(e) => {
            e.stopPropagation();
            onOpenDetails && onOpenDetails(movie);
          }}
          title="Movie Details"
        >
          <Info size={16} />
        </button>

        {/* Hover overlay with details */}
        <div className="card-hover-overlay">
          <div className="card-overlay-title">{displayTitle}</div>
          <div className="card-overlay-meta">
            <span>{year || 'N/A'}</span>
            {tmdb_rating ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: 'var(--accent-gold)' }}>
                <Star size={12} fill="currentColor" /> {tmdb_rating}
              </span>
            ) : null}
          </div>
          {genres && genres.length > 0 && (
            <div className="card-overlay-chips">
              {genres.slice(0, 2).map((g) => (
                <span key={g} className="card-mini-chip">
                  {g}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
