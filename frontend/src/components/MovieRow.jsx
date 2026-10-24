import React, { useRef, useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import MovieCard from './MovieCard';

export default function MovieRow({
  title,
  subtitle,
  movies = [],
  onSelectMovie,
  onOpenDetails,
  icon: Icon
}) {
  const trackRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (trackRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = trackRef.current;
      setCanScrollLeft(scrollLeft > 20);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 20);
    }
  };

  useEffect(() => {
    checkScroll();
    const el = trackRef.current;
    if (el) {
      el.addEventListener('scroll', checkScroll, { passive: true });
      window.addEventListener('resize', checkScroll);
    }
    return () => {
      if (el) el.removeEventListener('scroll', checkScroll);
      window.removeEventListener('resize', checkScroll);
    };
  }, [movies]);

  const handleScroll = (direction) => {
    if (trackRef.current) {
      const scrollAmount = trackRef.current.clientWidth * 0.75;
      trackRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (!movies || movies.length === 0) return null;

  return (
    <section className="carousel-section">
      <div className="carousel-header">
        <div className="carousel-title-group">
          <h2 className="carousel-heading">
            {Icon && <Icon size={20} style={{ color: 'var(--accent-gold)' }} />}
            {title}
          </h2>
          {subtitle && <p className="carousel-subtitle">{subtitle}</p>}
        </div>

        <div className="carousel-controls">
          <button
            className="carousel-arrow-btn"
            onClick={() => handleScroll('left')}
            disabled={!canScrollLeft}
            aria-label="Scroll row left"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            className="carousel-arrow-btn"
            onClick={() => handleScroll('right')}
            disabled={!canScrollRight}
            aria-label="Scroll row right"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="carousel-track" ref={trackRef}>
        {movies.map((movie) => (
          <MovieCard
            key={movie.movieId}
            movie={movie}
            onSelect={onSelectMovie}
            onOpenDetails={onOpenDetails}
          />
        ))}
      </div>
    </section>
  );
}
