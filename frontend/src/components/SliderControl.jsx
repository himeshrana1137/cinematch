import React from 'react';

export default function SliderControl({
  alpha,
  onChangeAlpha,
  disabled = false,
  isContentOnlyFallback = false
}) {
  const contentPercent = Math.round(alpha * 100);
  const collabPercent = 100 - contentPercent;

  return (
    <div className="controls-card">
      <div className="controls-header">
        <div className="controls-title">
          <span>⚙️</span> Hybrid Recommendation Weights
          {isContentOnlyFallback ? (
            <span className="badge-tag warning">
              ⚠️ Movie has &lt;5 ratings — using Content-only mode
            </span>
          ) : (
            <span className="badge-tag info">Live Model Blend</span>
          )}
        </div>

        <div className="slider-weights-display">
          <div className="weight-item">
            <span className="dot-content"></span>
            <span>Content: {contentPercent}%</span>
          </div>
          <div className="weight-item">
            <span className="dot-collab"></span>
            <span>Collaborative: {collabPercent}%</span>
          </div>
        </div>
      </div>

      <div className="slider-row">
        <span className="slider-label">
          Collaborative (Ratings)
        </span>

        <div className="slider-track-wrap">
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={alpha}
            disabled={disabled || isContentOnlyFallback}
            onChange={(e) => onChangeAlpha(parseFloat(e.target.value))}
            className="hybrid-slider"
            title={`Alpha = ${alpha.toFixed(2)}`}
          />
        </div>

        <span className="slider-label right">
          Content-based (Genres/Words)
        </span>
      </div>

      <div className="presets-row">
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Presets:</span>
        <button
          type="button"
          className={`preset-btn ${alpha === 0.0 && !isContentOnlyFallback ? 'active' : ''}`}
          onClick={() => onChangeAlpha(0.0)}
          disabled={disabled || isContentOnlyFallback}
        >
          Collaborative Only (0:100)
        </button>
        <button
          type="button"
          className={`preset-btn ${alpha === 0.25 && !isContentOnlyFallback ? 'active' : ''}`}
          onClick={() => onChangeAlpha(0.25)}
          disabled={disabled || isContentOnlyFallback}
        >
          Mostly Collab (25:75)
        </button>
        <button
          type="button"
          className={`preset-btn ${alpha === 0.5 && !isContentOnlyFallback ? 'active' : ''}`}
          onClick={() => onChangeAlpha(0.5)}
          disabled={disabled || isContentOnlyFallback}
        >
          Balanced Hybrid (50:50)
        </button>
        <button
          type="button"
          className={`preset-btn ${alpha === 0.75 && !isContentOnlyFallback ? 'active' : ''}`}
          onClick={() => onChangeAlpha(0.75)}
          disabled={disabled || isContentOnlyFallback}
        >
          Mostly Content (75:25)
        </button>
        <button
          type="button"
          className={`preset-btn ${alpha === 1.0 || isContentOnlyFallback ? 'active' : ''}`}
          onClick={() => onChangeAlpha(1.0)}
          disabled={disabled || isContentOnlyFallback}
        >
          Content Only (100:0)
        </button>
      </div>
    </div>
  );
}
