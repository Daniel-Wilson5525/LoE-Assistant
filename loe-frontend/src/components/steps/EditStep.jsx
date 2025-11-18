// src/components/steps/EditStep.jsx
import React, { useState, useEffect } from "react";

/** ---- helpers ---- */

// immutably set value at path: e.g. ["sites", 0, "name"]
function setAtPath(obj, path, value) {
  if (!path.length) return value;
  const [head, ...tail] = path;
  const clone = Array.isArray(obj) ? obj.slice() : { ...(obj || {}) };
  clone[head] = setAtPath(clone[head], tail, value);
  return clone;
}

// stop global key handlers eating space, etc.
const stopGlobalKeys = (e) => {
  e.stopPropagation();
};

/** ---- site card ---- */

function SiteCard({ index, site, onChange }) {
  const s = site || {};

  const set = (p, v) => onChange(p, v);

  const tasks = s.tasks || {};

  const renderTask = (key, label) => {
    const t = tasks[key] || {};
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">✔</span>
            <h4 className="h3" style={{ margin: 0 }}>
              {label}
            </h4>
          </div>
        </div>
        <div className="panel-body form-grid">
          <label className="field">
            <span className="label">Include</span>
            <input
              type="checkbox"
              checked={!!t.include}
              onChange={(e) => set(["tasks", key, "include"], e.target.checked)}
            />
          </label>
          <label className="field">
            <span className="label">Days</span>
            <input
              className="input"
              type="number"
              value={t.days ?? ""}
              onChange={(e) =>
                set(
                  ["tasks", key, "days"],
                  e.target.value === "" ? null : Number(e.target.value),
                )
              }
            />
          </label>
          <label className="field">
            <span className="label">Engineers</span>
            <input
              className="input"
              type="number"
              value={t.engineers ?? ""}
              onChange={(e) =>
                set(
                  ["tasks", key, "engineers"],
                  e.target.value === "" ? null : Number(e.target.value),
                )
              }
            />
          </label>
          <label className="field" style={{ gridColumn: "1 / -1" }}>
            <span className="label">Steps (one per line)</span>
            <textarea
              className="textarea"
              rows={3}
              value={(t.steps || []).join("\n")}
              onChange={(e) =>
                set(
                  ["tasks", key, "steps"],
                  e.target.value.split(/\r?\n/),
                )
              }
            />
          </label>
        </div>
      </div>
    );
  };

  const bom = s.bom || [];
  const optics = s.optics_bom || [];

  return (
    <div
      className="panel"
      style={{ borderColor: "var(--accent-border, #e0e7ff)" }}
    >
      <div className="panel-header">
        <div className="section-title">
          <span className="icon">{index + 1}</span>
          <h3 className="h3" style={{ margin: 0 }}>
            Site {index + 1} – {s.name || "Untitled"}
          </h3>
        </div>
      </div>

      <div className="panel-body space-y-3">
        {/* basic info */}
        <div className="form-grid">
          <label className="field">
            <span className="label">Name</span>
            <input
              className="input"
              value={s.name || ""}
              onChange={(e) => set(["name"], e.target.value)}
            />
          </label>
          <label className="field">
            <span className="label">Site ID</span>
            <input
              className="input"
              value={s.site_id || ""}
              onChange={(e) => set(["site_id"], e.target.value)}
            />
          </label>
          <label className="field">
            <span className="label">Country</span>
            <input
              className="input"
              value={s.country || ""}
              onChange={(e) => set(["country"], e.target.value)}
            />
          </label>
        </div>

        <label className="field">
          <span className="label">Address</span>
          <textarea
            className="textarea"
            rows={2}
            value={s.address || ""}
            onChange={(e) => set(["address"], e.target.value)}
          />
        </label>

        {/* site assumptions / constraints */}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          }}
        >
          <div className="field">
            <span className="label">Assumptions</span>
            <textarea
              className="textarea"
              rows={3}
              value={(s.assumptions || []).join("\n")}
              onChange={(e) =>
                set(["assumptions"], e.target.value.split(/\r?\n/))
              }
            />
          </div>
          <div className="field">
            <span className="label">Constraints</span>
            <textarea
              className="textarea"
              rows={3}
              value={(s.constraints || []).join("\n")}
              onChange={(e) =>
                set(["constraints"], e.target.value.split(/\r?\n/))
              }
            />
          </div>
        </div>

        {/* BOM + optics */}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "2fr 1fr",
          }}
        >
          {/* BOM */}
          <div className="panel">
            <div className="panel-header">
              <div className="section-title">
                <span className="icon">📦</span>
                <h4 className="h3" style={{ margin: 0 }}>
                  BOM
                </h4>
              </div>
            </div>
            <div className="panel-body" style={{ display: "grid", gap: 8 }}>
              {bom.map((row, i) => (
                <div key={i} className="form-grid">
                  <label className="field">
                    <span className="label">Model</span>
                    <input
                      className="input"
                      value={row.model || ""}
                      onChange={(e) => {
                        const next = bom.slice();
                        next[i] = { ...row, model: e.target.value };
                        set(["bom"], next);
                      }}
                    />
                  </label>
                  <label className="field">
                    <span className="label">Type</span>
                    <input
                      className="input"
                      value={row.type || ""}
                      onChange={(e) => {
                        const next = bom.slice();
                        next[i] = { ...row, type: e.target.value };
                        set(["bom"], next);
                      }}
                    />
                  </label>
                  <label className="field">
                    <span className="label">Qty</span>
                    <input
                      className="input"
                      type="number"
                      value={row.qty ?? ""}
                      onChange={(e) => {
                        const next = bom.slice();
                        next[i] = {
                          ...row,
                          qty:
                            e.target.value === ""
                              ? null
                              : Number(e.target.value),
                        };
                        set(["bom"], next);
                      }}
                    />
                  </label>
                  <label className="field" style={{ gridColumn: "1 / -1" }}>
                    <span className="label">Notes</span>
                    <textarea
                      className="textarea"
                      rows={2}
                      value={row.notes || ""}
                      onChange={(e) => {
                        const next = bom.slice();
                        next[i] = { ...row, notes: e.target.value };
                        set(["bom"], next);
                      }}
                    />
                  </label>
                </div>
              ))}
              <div
                className="panel-actions"
                style={{ justifyContent: "flex-end" }}
              >
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    set(["bom"], [
                      ...bom,
                      { model: "", type: "", qty: null, notes: "" },
                    ])
                  }
                >
                  + Add Item
                </button>
              </div>
            </div>
          </div>

          {/* optics */}
          <div className="panel">
            <div className="panel-header">
              <div className="section-title">
                <span className="icon">🔌</span>
                <h4 className="h3" style={{ margin: 0 }}>
                  Optics
                </h4>
              </div>
            </div>
            <div className="panel-body" style={{ display: "grid", gap: 8 }}>
              {optics.map((row, i) => (
                <div key={i} className="form-grid">
                  <label className="field">
                    <span className="label">Model</span>
                    <input
                      className="input"
                      value={row.model || ""}
                      onChange={(e) => {
                        const next = optics.slice();
                        next[i] = { ...row, model: e.target.value };
                        set(["optics_bom"], next);
                      }}
                    />
                  </label>
                  <label className="field">
                    <span className="label">Type</span>
                    <input
                      className="input"
                      value={row.type || ""}
                      onChange={(e) => {
                        const next = optics.slice();
                        next[i] = { ...row, type: e.target.value };
                        set(["optics_bom"], next);
                      }}
                    />
                  </label>
                </div>
              ))}
              <div
                className="panel-actions"
                style={{ justifyContent: "flex-end" }}
              >
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    set(["optics_bom"], [
                      ...optics,
                      { model: "", type: "Optics", qty: null, notes: "" },
                    ])
                  }
                >
                  + Add Optic
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* tasks */}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          }}
        >
          {renderTask("site_survey", "Site Survey")}
          {renderTask("installation", "Installation")}
          {renderTask("optics_installation", "Optics Installation")}
          {renderTask("post_install", "Post-install")}
        </div>
      </div>
    </div>
  );
}

/** ---- main schema editor ---- */

function SchemaEditor({ schema, onSchemaChange }) {
  const s = schema || {};

  const set = (path, value) => {
    onSchemaChange(setAtPath(s, path, value));
  };

  const sites = s.sites || [];

  return (
    <div className="space-y-4">
      {/* PROJECT OVERVIEW */}
      <div className="panel">
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">📋</span>
            <h3 className="h3" style={{ margin: 0 }}>
              Project Overview
            </h3>
          </div>
        </div>
        <div
          className="panel-body"
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          }}
        >
          {/* col 1 */}
          <div className="form-grid">
            <label className="field">
              <span className="label">Client</span>
              <input
                className="input"
                value={s.client || ""}
                onChange={(e) => set(["client"], e.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Project Name</span>
              <input
                className="input"
                value={s.project_name || ""}
                onChange={(e) => set(["project_name"], e.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Service</span>
              <input
                className="input"
                value={s.service || ""}
                onChange={(e) => set(["service"], e.target.value)}
              />
            </label>
          </div>

          {/* col 2 */}
          <div className="form-grid">
            <label className="field">
              <span className="label">Scope</span>
              <input
                className="input"
                value={s.scope || ""}
                onChange={(e) => set(["scope"], e.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Environment</span>
              <input
                className="input"
                value={s.environment || ""}
                onChange={(e) => set(["environment"], e.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Timeline</span>
              <input
                className="input"
                value={s.timeline || ""}
                onChange={(e) => set(["timeline"], e.target.value)}
              />
            </label>
          </div>

          {/* col 3 */}
          <div className="form-grid">
            <label className="field">
              <span className="label">LoE Type</span>
              <input className="input" value={s.loe_type || ""} readOnly />
            </label>
            <label className="field">
              <span className="label">Devices Total</span>
              <input
                className="input"
                type="number"
                value={s.counts?.devices_total ?? ""}
                onChange={(e) =>
                  set(
                    ["counts", "devices_total"],
                    e.target.value === "" ? null : Number(e.target.value),
                  )
                }
              />
            </label>
            <label className="field">
              <span className="label">Engineer Days</span>
              <input
                className="input"
                type="number"
                value={s.effort_summary?.totals?.engineer_days ?? ""}
                onChange={(e) =>
                  set(
                    ["effort_summary", "totals", "engineer_days"],
                    e.target.value === "" ? null : Number(e.target.value),
                  )
                }
              />
            </label>
          </div>
        </div>

        <div className="panel-body">
          <label className="field" style={{ gridColumn: "1 / -1" }}>
            <span className="label">Notes Raw (email)</span>
            <textarea
              className="textarea font-mono"
              rows={6}
              value={s.notes_raw || ""}
              onChange={(e) => set(["notes_raw"], e.target.value)}
              onKeyDown={stopGlobalKeys}
            />
          </label>
        </div>
      </div>

      {/* ASSUMPTIONS / CONSTRAINTS */}
      <div className="edit-grid">
        <div className="panel panel-compact">
          <div className="panel-header">
            <div className="section-title">
              <span className="icon">💡</span>
              <h3 className="h3" style={{ margin: 0 }}>
                Assumptions
              </h3>
            </div>
            <p className="hint">One item per line</p>
          </div>
          <div className="panel-body">
            <textarea
              className="textarea"
              rows={4}
              value={(s.assumptions || []).join("\n")}
              onChange={(e) =>
                set(["assumptions"], e.target.value.split(/\r?\n/))
              }
            />
          </div>
        </div>

        <div className="panel panel-compact">
          <div className="panel-header">
            <div className="section-title">
              <span className="icon">⚠️</span>
              <h3 className="h3" style={{ margin: 0 }}>
                Constraints
              </h3>
            </div>
            <p className="hint">One item per line</p>
          </div>
          <div className="panel-body">
            <textarea
              className="textarea"
              rows={4}
              value={(s.constraints || []).join("\n")}
              onChange={(e) =>
                set(["constraints"], e.target.value.split(/\r?\n/))
              }
            />
          </div>
        </div>
      </div>

      {/* GLOBAL SCOPE + GOVERNANCE/HANDOVER */}
      <div className="edit-grid">
        {/* global scope */}
        <div className="panel panel-compact">
          <div className="panel-header">
            <div className="section-title">
              <span className="icon">🌐</span>
              <h3 className="h3" style={{ margin: 0 }}>
                Global Scope
              </h3>
            </div>
          </div>
          <div
            className="panel-body"
            style={{ display: "grid", gap: 8 }}
          >
            {["rack_and_stack", "site_survey", "optics_installation", "post_install"].map(
              (key) => {
                const row = s.global_scope?.[key] || {};
                const label = key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (m) => m.toUpperCase());
                return (
                  <div key={key} className="field">
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={!!row.include}
                        onChange={(e) =>
                          set(
                            ["global_scope", key, "include"],
                            e.target.checked,
                          )
                        }
                      />
                      <span className="label">{label}</span>
                    </div>
                    <textarea
                      className="textarea"
                      rows={2}
                      placeholder="Notes (optional)"
                      value={row.notes || ""}
                      onChange={(e) =>
                        set(
                          ["global_scope", key, "notes"],
                          e.target.value,
                        )
                      }
                    />
                  </div>
                );
              },
            )}
          </div>
        </div>

        {/* governance + handover */}
        <div className="panel panel-compact">
          <div className="panel-header">
            <div className="section-title">
              <span className="icon">🤝</span>
              <h3 className="h3" style={{ margin: 0 }}>
                Governance &amp; Handover
              </h3>
            </div>
          </div>
          <div className="panel-body form-grid">
            <label className="field">
              <span className="label">PM</span>
              <input
                className="input"
                value={s.governance?.pm || ""}
                onChange={(e) => set(["governance", "pm"], e.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Comms Channels</span>
              <input
                className="input"
                value={s.governance?.comms_channels || ""}
                onChange={(e) =>
                  set(["governance", "comms_channels"], e.target.value)
                }
              />
            </label>
            <label className="field">
              <span className="label">Escalation</span>
              <input
                className="input"
                value={s.governance?.escalation || ""}
                onChange={(e) =>
                  set(["governance", "escalation"], e.target.value)
                }
              />
            </label>
            <label className="field">
              <span className="label">Handover Docs</span>
              <input
                className="input"
                value={s.handover?.docs || ""}
                onChange={(e) => set(["handover", "docs"], e.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Acceptance Criteria</span>
              <textarea
                className="textarea"
                rows={3}
                value={s.handover?.acceptance_criteria || ""}
                onChange={(e) =>
                  set(
                    ["handover", "acceptance_criteria"],
                    e.target.value,
                  )
                }
              />
            </label>
          </div>
        </div>
      </div>

      {/* SITES */}
      <div className="panel">
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">🏢</span>
            <h3 className="h3" style={{ margin: 0 }}>
              Sites
            </h3>
          </div>
          <p className="hint">One card per site</p>
        </div>
        <div
          className="panel-body"
          style={{ display: "grid", gap: 16 }}
        >
          {sites.map((site, idx) => (
            <SiteCard
              key={idx}
              index={idx}
              site={site}
              onChange={(path, value) => {
                const fullPath = ["sites", idx, ...path];
                set(fullPath, value);
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}


/** ---- main step component ---- */

export default function EditStep({ schema, onSchemaChange, onNext }) {
  const [jsonText, setJsonText] = useState(
    () => JSON.stringify(schema, null, 2),
  );
  const [jsonErr, setJsonErr] = useState("");

  useEffect(() => {
    setJsonErr("");
    setJsonText(JSON.stringify(schema, null, 2));
  }, [schema]);

  const applyJson = () => {
    try {
      const next = JSON.parse(jsonText);
      setJsonErr("");
      onSchemaChange(next);
    } catch (e) {
      setJsonErr(e.message || "Invalid JSON");
    }
  };

  return (
    <div className="max-w-5xl space-y-4">
      {/* structured editor */}
      <SchemaEditor schema={schema} onSchemaChange={onSchemaChange} />

      {/* raw JSON editor */}
      <div className="panel">
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">{"</>"}</span>
            <h3 className="h3" style={{ margin: 0 }}>
              Full Schema (JSON)
            </h3>
          </div>
          <p className="hint">
            Edit directly if easier. Changes here update the same schema above.
          </p>
        </div>
        <div className="panel-body">
          {jsonErr && (
            <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 mb-3">
              {jsonErr}
            </div>
          )}
          <textarea
            className="textarea font-mono"
            rows={16}
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            onKeyDown={stopGlobalKeys}
            spellCheck={false}
            autoComplete="off"
            style={{ whiteSpace: "pre-wrap" }}
          />
          <div
            className="panel-actions"
            style={{ justifyContent: "flex-end", marginTop: 8 }}
          >
            <button className="btn" type="button" onClick={applyJson}>
              Apply JSON
            </button>
          </div>
        </div>
      </div>

      {/* generate */}
      <div className="panel">
        <div
          className="panel-body"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 12,
          }}
        >
          <span className="hint">
            Review/edit all fields above, then generate your LoE.
          </span>
          <button
            className="btn"
            type="button"
            onClick={(e) => {
              e.preventDefault();
              onNext?.();
            }}
          >
            Generate
          </button>
        </div>
      </div>
    </div>
  );
}
