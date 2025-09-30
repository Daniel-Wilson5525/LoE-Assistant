import React from "react";
import { useState } from "react";
import { ingestLoE } from "../../lib/api";

export default function PasteStep({ onIngested, defaultLoeType = "rack_stack" }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const submit = async () => {
    setErr(""); setLoading(true);
    try {
      const { schema } = await ingestLoE(text, defaultLoeType);
      onIngested(schema);
    } catch (e) {
      setErr(e.message || "Failed to ingest");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <label className="block text-sm font-medium mb-2">Paste client request / notes</label>
      <textarea
        className="w-full min-h-[220px] rounded-lg border border-slate-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Paste email or request text here…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      {err && <p className="text-red-600 mt-2">{err}</p>}
      <div className="mt-4">
        <button
          onClick={submit}
          disabled={loading || !text.trim()}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50"
        >
          {loading ? "Extracting…" : "Extract fields"}
        </button>
      </div>
    </div>
  );
}
