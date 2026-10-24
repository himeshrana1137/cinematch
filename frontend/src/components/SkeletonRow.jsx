import React from 'react';

export default function SkeletonRow({ count = 6, title = "Loading titles..." }) {
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <section className="carousel-section">
      <div className="carousel-header">
        <h2 className="carousel-heading" style={{ opacity: 0.6 }}>{title}</h2>
      </div>
      <div className="carousel-track">
        {items.map((i) => (
          <div key={i} className="cinema-skeleton-card card-shimmer" />
        ))}
      </div>
    </section>
  );
}
