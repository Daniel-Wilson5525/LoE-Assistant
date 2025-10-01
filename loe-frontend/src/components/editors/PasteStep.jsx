import React, { useState } from "react";
import { ingestLoE } from "../../lib/api";
import { DEFAULT_SCHEMA } from "../../lib/schema"; // if this export differs, swap accordingly

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
      setErr(e.message || "Failed to extract fields");
    } finally {
      setLoading(false);
    }
  };

  const skipManual = () => {
    // fall back to a minimal schema if DEFAULT_SCHEMA isn’t available
    const base = DEFAULT_SCHEMA || {
      loe_type: defaultLoeType,
      client: "",
      project_name: "",
      service: "",
      scope: "",
      environment: "",
      timeline: "",
      sites: [{ name: "", address: "" }],
      devices: [],
      bom: [],
      deliverables: [],
      constraints: [],
      notes_raw: "",
      staging: {},
      rollout: {},
      counts: {},
    };
    onIngested({ ...base, loe_type: defaultLoeType });
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100">
        <h2 className="text-lg font-semibold">Paste email text (or leave empty to proceed to manual entry)</h2>
        <p className="text-sm text-slate-500">We’ll extract client, sites, devices/BOM, staging and rollout hints.</p>
      </div>

      {/* Body */}
      <div className="px-6 py-5 space-y-3">
        {err && (
          <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800">
            {err}
          </div>
        )}

        <label className="text-sm font-medium text-slate-700">Email / Request</label>
        <textarea
          className="w-full min-h-[260px] rounded-xl border border-slate-300 bg-slate-50/50 focus:bg-white p-4 font-mono text-sm outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Paste the client email content here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
          <button
            onClick={submit}
            disabled={loading || !text.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 text-white disabled:opacity-50"
          >
            {loading && (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/60 border-t-transparent" />
            )}
            {loading ? "Extracting…" : "Extract fields"}
          </button>

          <button
            onClick={skipManual}
            className="px-4 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800"
          >
            Skip &amp; fill fields manually
          </button>
        </div>
      </div>
    </div>
  );
}
