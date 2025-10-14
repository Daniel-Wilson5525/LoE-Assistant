// src/lib/api.js
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5050";

async function _json(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText} — ${text || "no body"}`);
  }
  return res.json();
}

// ---- SINGLE-FLIGHT: dedupe concurrent/duplicate calls with identical body ----
const inflight = new Map(); // key: stringified body -> Promise

function singleFlightFetch(url, options) {
  const key = JSON.stringify({ url, body: options?.body || "" });
  if (inflight.has(key)) return inflight.get(key);

  const p = fetch(url, options)
    .then(_json)
    .finally(() => inflight.delete(key));

  inflight.set(key, p);
  return p;
}

// ------------------ public API ------------------

export async function ingestText(text, loeType) {
  return singleFlightFetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, loe_type: loeType }),
  });
}

export async function generateLoE(schema, loeType) {
  return singleFlightFetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema, loe_type: loeType || schema?.loe_type }),
  });
}
