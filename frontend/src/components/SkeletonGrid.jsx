import React from 'react';

export default function SkeletonGrid({ count = 10 }) {
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <div className="movie-grid">
      {items.map((i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-poster skeleton-pulse"></div>
          <div className="skeleton-body">
            <div className="skeleton-line title skeleton-pulse"></div>
            <div className="skeleton-line sub skeleton-pulse"></div>
            <div className="skeleton-line sub skeleton-pulse" style={{ width: '60%' }}></div>
          </div>
        </div>
      ))}
    </div>
  );
}
