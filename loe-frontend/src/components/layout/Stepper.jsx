// src/components/layout/Stepper.jsx
import React, { useMemo, useCallback } from "react";

/**
 * Horizontal, accessible Stepper
 * Props:
 *  - steps: [{ key: '1', label: 'Paste' }, ...]
 *  - currentKey: '1' | '2' | '3'
 *  - onStepChange: (key) => void
 */
export default function Stepper({ steps = [], currentKey, onStepChange }) {
  const currentIndex = Math.max(
    0,
    steps.findIndex((s) => String(s.key) === String(currentKey))
  );

  const go = useCallback(
    (idx) => {
      const s = steps[idx];
      if (s) onStepChange?.(s.key);
    },
    [steps, onStepChange]
  );

  return (
    <nav className="stepper" aria-label="Progress">
      <ol className="stepper-list" role="list">
        {steps.map((s, i) => {
          const isActive = i === currentIndex;
          const isComplete = i < currentIndex;

          return (
            <li key={s.key} className="stepper-item">
              {/* progress line (left) */}
              {i > 0 && (
                <span
                  className={`stepper-line ${i <= currentIndex ? "is-filled" : ""}`}
                  aria-hidden="true"
                />
              )}

              {/* step button */}
              <button
                type="button"
                className={`stepper-btn ${isActive ? "is-active" : ""} ${isComplete ? "is-complete" : ""}`}
                aria-current={isActive ? "step" : undefined}
                aria-label={`Step ${i + 1}: ${s.label}`}
                onClick={() => go(i)}
                onKeyDown={(e) => {
                  if (e.key === "ArrowRight") { e.preventDefault(); go(i + 1); }
                  if (e.key === "ArrowLeft")  { e.preventDefault(); go(i - 1); }
                }}
              >
                <span className="stepper-index" aria-hidden="true">{i + 1}</span>
                <span className="stepper-label">{s.label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
