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

  const canExtract = !!text.trim();

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="section-title">
          <span className="icon">📥</span>
          <h2 className="h2">Paste Email / Request</h2>
        </div>
        <p className="hint">
          We’ll extract client, sites, devices/BOM, staging and rollout hints. You can refine everything on the next step.
        </p>
      </div>

      <div className="panel-body">
        {err && (
          <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 mb-3">
            {err}
          </div>
        )}

        <div className="field" style={{ gridColumn: "1 / -1" }}>
          <label className="label">Email / Request</label>
          <textarea
            className="textarea font-mono"
            style={{ minHeight: 260 }}
            placeholder="Paste the client email content here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
          />
          <div className="flex items-center justify-between">
            <span className="hint">{text.length.toLocaleString()} characters</span>
            {!canExtract && <span className="hint"> You can also skip and fill fields manually.</span>}
          </div>
        </div>

        <div className="panel-divider" />

        <div className="panel-actions">
          <button
            onClick={submit}
            disabled={loading || !canExtract}
            className="btn"
            aria-busy={loading}
          >
            {loading ? "Extracting…" : "Extract fields"}
          </button>
          <button
            onClick={skipManual}
            className="btn-secondary"
            disabled={loading}
          >
            Skip &amp; fill fields manually
          </button>
        </div>
      </div>
    </div>
  );
}
