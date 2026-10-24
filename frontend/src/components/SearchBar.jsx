import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Film, Star } from 'lucide-react';
import { formatTitle } from '../utils/format';

export default function SearchBar({ onSelectMovie }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isMobileExpanded, setIsMobileExpanded] = useState(false);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  // Debounced search effect (300 ms)
  useEffect(() => {
    if (!searchTerm.trim()) {
      setResults([]);
      setIsOpen(false);
      setIsLoading(false);
      setActiveIndex(-1);
      return;
    }

    setIsLoading(true);
    const handler = setTimeout(async () => {
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(searchTerm.trim())}`);
        if (response.ok) {
          const data = await response.json();
          setResults(data);
          setIsOpen(true);
          setActiveIndex(-1);
        } else {
          setResults([]);
        }
      } catch (err) {
        console.error('Search fetch error:', err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Click outside to close dropdown and collapse mobile search
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
        if (!searchTerm) {
          setIsMobileExpanded(false);
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [searchTerm]);

  const handleSelect = (movie) => {
    setIsOpen(false);
    setSearchTerm('');
    setActiveIndex(-1);
    setIsMobileExpanded(false);
    if (onSelectMovie) {
      onSelectMovie(movie);
    }
  };

  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < results.length) {
        handleSelect(results[activeIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setIsMobileExpanded(false);
    }
  };

  const handleTriggerMobileExpand = () => {
    setIsMobileExpanded(true);
    setTimeout(() => {
      if (inputRef.current) inputRef.current.focus();
    }, 50);
  };

  return (
    <div className={`navbar-search-center ${isMobileExpanded ? 'mobile-expanded' : ''}`} ref={wrapperRef}>
      {/* Mobile collapse trigger button */}
      <button
        className="mobile-search-trigger-btn"
        onClick={handleTriggerMobileExpand}
        aria-label="Open search"
      >
        <Search size={18} />
      </button>

      <div className="search-pill-box">
        <span className="search-input-lead">
          <Search size={18} />
        </span>
        <input
          ref={inputRef}
          type="text"
          className="search-pill-input"
          placeholder="Search by title, franchise, or genre..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => {
            setIsMobileExpanded(true);
            if (results.length > 0) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          aria-label="Search movies"
        />
        {(searchTerm || isMobileExpanded) && (
          <button
            className="search-input-clear"
            onClick={() => {
              setSearchTerm('');
              setResults([]);
              setIsOpen(false);
              setIsMobileExpanded(false);
            }}
            aria-label="Close search"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="search-glass-dropdown" role="listbox">
          {isLoading && (
            <div className="dropdown-status-box">Searching catalog...</div>
          )}

          {!isLoading && results.length === 0 && (
            <div className="dropdown-status-box">No movies found matching "{searchTerm}"</div>
          )}

          {!isLoading && results.length > 0 && (
            <div>
              {results.map((movie, index) => {
                const formattedTitle = formatTitle(movie.title);
                return (
                  <div
                    key={movie.movieId}
                    className={`dropdown-movie-row ${index === activeIndex ? 'highlighted' : ''}`}
                    onClick={() => handleSelect(movie)}
                    role="option"
                    aria-selected={index === activeIndex}
                  >
                    <div className="dropdown-thumb-placeholder">
                      <Film size={18} />
                    </div>
                    <div className="dropdown-info">
                      <div className="dropdown-movie-title">{formattedTitle}</div>
                      <div className="dropdown-movie-meta">
                        <span>{movie.year || 'N/A'}</span>
                        {movie.genres && movie.genres.length > 0 && (
                          <span>• {movie.genres.slice(0, 2).join(', ')}</span>
                        )}
                      </div>
                    </div>
                    {movie.rating_count ? (
                      <span className="dropdown-rating-pill">
                        <Star size={11} fill="currentColor" /> {movie.rating_count}
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
