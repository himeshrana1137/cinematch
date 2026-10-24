import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, Sparkles, Star, Clock, User, Film } from 'lucide-react';
import { formatTitle, formatRuntime } from '../utils/format';

export default function DetailModal({
  movie,
  isOpen,
  onClose,
  onFindSimilar,
  initialPlayTrailer = false
}) {
  const [isPlayingTrailer, setIsPlayingTrailer] = useState(initialPlayTrailer);

  useEffect(() => {
    setIsPlayingTrailer(initialPlayTrailer);
  }, [initialPlayTrailer, movie]);

  // Lock body scroll and listen for Escape key
  useEffect(() => {
    if (!isOpen) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !movie) return null;

  const {
    title,
    year,
    genres = [],
    poster_url,
    backdrop_url,
    overview,
    tagline,
    runtime,
    tmdb_rating,
    cast = [],
    trailer_key
  } = movie;

  const displayTitle = formatTitle(title);

  return (
    <AnimatePresence>
      <div
        className="modal-overlay"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-movie-title"
      >
        <motion.div
          className="modal-dialog"
          initial={{ opacity: 0, scale: 0.92, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          {/* Close button */}
          <button
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close details modal"
          >
            <X size={20} />
          </button>

          {/* Backdrop Header */}
          <div className="modal-backdrop-header">
            {backdrop_url ? (
              <img
                src={backdrop_url}
                alt={displayTitle}
                className="modal-backdrop-img"
              />
            ) : (
              <div style={{ width: '100%', height: '100%', background: '#1c1c28' }} />
            )}
            <div className="modal-backdrop-gradient" />
          </div>

          {/* Modal Main Body */}
          <div className="modal-body">
            <div className="modal-top-grid">
              <div className="modal-poster-wrap">
                {poster_url ? (
                  <img src={poster_url} alt={displayTitle} className="modal-poster-img" />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#181824' }}>
                    <Film size={32} />
                  </div>
                )}
              </div>

              <div className="modal-header-info">
                <h2 id="modal-movie-title" className="modal-title">{displayTitle}</h2>
                {tagline && <p className="modal-tagline">"{tagline}"</p>}

                <div className="modal-meta-row">
                  {tmdb_rating ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-gold)' }}>
                      <Star size={15} fill="currentColor" /> {tmdb_rating} TMDB
                    </span>
                  ) : null}

                  {year && <span>{year}</span>}

                  {runtime ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                      <Clock size={14} /> {formatRuntime(runtime)}
                    </span>
                  ) : null}
                </div>

                {genres && genres.length > 0 && (
                  <div className="modal-genres">
                    {genres.map((g) => (
                      <span key={g} className="hero-genre-chip">
                        {g}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Overview */}
            {overview && <p className="modal-overview">{overview}</p>}

            {/* YouTube Trailer Section */}
            {isPlayingTrailer ? (
              <div className="trailer-embed-container">
                {trailer_key ? (
                  <iframe
                    className="trailer-iframe"
                    src={`https://www.youtube-nocookie.com/embed/${trailer_key}?autoplay=1&rel=0`}
                    title={`${displayTitle} Trailer`}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Official trailer is not available on YouTube for this title.
                  </div>
                )}
              </div>
            ) : (
              trailer_key && (
                <div style={{ marginBottom: '1.75rem' }}>
                  <button
                    className="btn-primary-gradient"
                    onClick={() => setIsPlayingTrailer(true)}
                  >
                    <Play size={16} fill="currentColor" />
                    <span>Watch Official Trailer</span>
                  </button>
                </div>
              )
            )}

            {/* Cast Avatars */}
            {cast && cast.length > 0 && (
              <div>
                <h3 className="modal-section-title">
                  <User size={16} /> Featured Cast
                </h3>
                <div className="cast-grid">
                  {cast.map((actor, idx) => (
                    <div key={idx} className="cast-card">
                      {actor.profile_url ? (
                        <img
                          src={actor.profile_url}
                          alt={actor.name}
                          className="cast-avatar"
                          loading="lazy"
                        />
                      ) : (
                        <div className="cast-avatar-fallback">
                          <User size={24} />
                        </div>
                      )}
                      <div className="cast-name">{actor.name}</div>
                      <div className="cast-character">{actor.character}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions footer */}
            <div className="modal-actions-footer">
              <button
                className="btn-primary-gradient"
                onClick={() => {
                  onClose();
                  onFindSimilar && onFindSimilar(movie);
                }}
              >
                <Sparkles size={16} />
                <span>Find Similar Recommendations</span>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
