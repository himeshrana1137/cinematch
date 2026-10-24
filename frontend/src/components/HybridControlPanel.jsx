import React, { useState } from 'react';
import { SlidersHorizontal, HelpCircle, AlertCircle } from 'lucide-react';

export default function HybridControlPanel({
  alpha,
  onChangeAlpha,
  onCommitAlpha,
  disabled = false,
  isContentOnlyFallback = false
}) {
  const [showTooltip, setShowTooltip] = useState(false);

  const contentPercent = Math.round(alpha * 100);
  const collabPercent = 100 - contentPercent;

  const handlePreset = (val) => {
    onChangeAlpha(val);
    onCommitAlpha(val);
  };

  return (
    <section className="hybrid-panel-section" id="hybrid-controls">
      <div className="hybrid-panel-card">
        <div className="panel-header-row">
          <div className="panel-title-wrap">
            <SlidersHorizontal size={20} style={{ color: 'var(--accent-violet)' }} />
            <h3 className="panel-title">Hybrid Recommendation Weights</h3>

            <div
              className="tooltip-trigger"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              onClick={() => setShowTooltip((p) => !p)}
              aria-label="Algorithm information"
            >
              <HelpCircle size={16} />
              {showTooltip && (
                <div className="tooltip-popup">
                  Hybrid scoring merges Content-Based Filtering (TF-IDF genre and title keywords) with Collaborative Filtering (TruncatedSVD user rating embeddings). Adjusting the slider balances storyline &amp; theme matches against community viewing behavior.
                </div>
              )}
            </div>
          </div>

          <div className="live-weights-pills">
            {isContentOnlyFallback ? (
              <div className="weight-pill" style={{ color: 'var(--accent-gold)' }}>
                <AlertCircle size={14} />
                <span>&lt; 5 ratings: 100% Content</span>
              </div>
            ) : (
              <>
                <div className="weight-pill">
                  <span className="weight-dot-violet"></span>
                  <span>Content: {contentPercent}%</span>
                </div>
                <div className="weight-pill">
                  <span className="weight-dot-gold"></span>
                  <span>Collaborative: {collabPercent}%</span>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="slider-track-container">
          <span className="slider-endpoint-label">
            Collaborative (User Ratings)
          </span>

          <div className="range-input-wrapper">
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={alpha}
              disabled={disabled || isContentOnlyFallback}
              onChange={(e) => onChangeAlpha(parseFloat(e.target.value))}
              onPointerUp={(e) => onCommitAlpha(parseFloat(e.target.value))}
              onKeyUp={(e) => onCommitAlpha(parseFloat(e.target.value))}
              className="cinematic-range-input"
              aria-label="Hybrid recommendation balance slider"
            />
          </div>

          <span className="slider-endpoint-label right">
            Content-based (Genres &amp; Words)
          </span>
        </div>

        <div className="presets-container">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Presets:</span>
          <button
            type="button"
            className={`preset-chip-btn ${alpha === 0.0 && !isContentOnlyFallback ? 'active' : ''}`}
            onClick={() => handlePreset(0.0)}
            disabled={disabled || isContentOnlyFallback}
          >
            Collaborative Only (0:100)
          </button>
          <button
            type="button"
            className={`preset-chip-btn ${alpha === 0.25 && !isContentOnlyFallback ? 'active' : ''}`}
            onClick={() => handlePreset(0.25)}
            disabled={disabled || isContentOnlyFallback}
          >
            Mostly Collab (25:75)
          </button>
          <button
            type="button"
            className={`preset-chip-btn ${alpha === 0.5 && !isContentOnlyFallback ? 'active' : ''}`}
            onClick={() => handlePreset(0.5)}
            disabled={disabled || isContentOnlyFallback}
          >
            Balanced Hybrid (50:50)
          </button>
          <button
            type="button"
            className={`preset-chip-btn ${alpha === 0.75 && !isContentOnlyFallback ? 'active' : ''}`}
            onClick={() => handlePreset(0.75)}
            disabled={disabled || isContentOnlyFallback}
          >
            Mostly Content (75:25)
          </button>
          <button
            type="button"
            className={`preset-chip-btn ${alpha === 1.0 || isContentOnlyFallback ? 'active' : ''}`}
            onClick={() => handlePreset(1.0)}
            disabled={disabled || isContentOnlyFallback}
          >
            Content Only (100:0)
          </button>
        </div>
      </div>
    </section>
  );
}
