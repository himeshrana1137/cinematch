import React, { useState } from 'react';

export default function SelectedMovieHero({ movie, onClear }) {
  const [imgError, setImgError] = useState(false);

  if (!movie) return null;

  const {
    title,
    year,
    genres = [],
    poster_url,
    overview,
    tmdb_rating,
    rating_count,
    rating_mean
  } = movie;

  const hasPoster = poster_url && !imgError;

  return (
    <div className="selected-hero-card">
      <div className="hero-poster-wrap">
        {hasPoster ? (
          <img
            src={poster_url}
            alt={title}
            className="hero-poster-img"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="card-poster-placeholder" style={{ height: '100%' }}>
            <span className="placeholder-icon">🎬</span>
            <span className="placeholder-title">{title}</span>
            {year && <span style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>({year})</span>}
          </div>
        )}
      </div>

      <div className="hero-content">
        <div>
          <div className="hero-top-badge">
            <span>✨</span> Because you picked
          </div>

          <h2 className="hero-title">
            {title}
          </h2>

          <div className="hero-meta">
            {year && <span className="hero-year">{year}</span>}

            {tmdb_rating !== undefined && tmdb_rating !== null && (
              <span className="hero-rating" title="TMDB Community Score">
                <span>★</span> {tmdb_rating} TMDB
              </span>
            )}

            {rating_mean ? (
              <span className="hero-rating-count" title="MovieLens Mean Rating">
                Avg Rating: {rating_mean} / 5.0
              </span>
            ) : null}

            {rating_count !== undefined && (
              <span className="hero-rating-count">
                ({rating_count} MovieLens reviews)
              </span>
            )}
          </div>

          {genres && genres.length > 0 && (
            <div className="card-genres" style={{ marginBottom: '1rem' }}>
              {genres.map((g) => (
                <span key={g} className="genre-chip" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>
                  {g}
                </span>
              ))}
            </div>
          )}

          <p className="hero-overview">
            {overview || 'No synopsis available for this title.'}
          </p>
        </div>

        <div className="hero-actions">
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Showing top recommendations below based on content similarity and viewer tastes.
          </span>
          <button className="reset-btn" onClick={onClear} title="Return to popular movies">
            <span>✕</span> Clear Selection (Back to Popular)
          </button>
        </div>
      </div>
    </div>
  );
}
