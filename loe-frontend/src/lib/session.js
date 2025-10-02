// src/lib/session.js
import { useState, useEffect, useRef } from "react";

/** Persist a value in sessionStorage (clears when the tab closes). */
export function useSessionState(key, initialValue) {
  const isFirst = useRef(true);
  const [value, setValue] = useState(() => {
    try {
      const raw = sessionStorage.getItem(key);
      return raw != null ? JSON.parse(raw) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    // skip writing the initial load if it came from storage
    if (isFirst.current) { isFirst.current = false; return; }
    try {
      if (value === undefined || value === null) sessionStorage.removeItem(key);
      else sessionStorage.setItem(key, JSON.stringify(value));
    } catch { /* ignore quota errors */ }
  }, [key, value]);

  return [value, setValue];
}

/** Convenience: clear one or more session keys */
export function clearSessionKeys(...keys) {
  for (const k of keys) sessionStorage.removeItem(k);
}
