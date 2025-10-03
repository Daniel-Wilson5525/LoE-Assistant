import React, { useMemo, useState, useEffect } from "react";

/** -------- helpers -------- */
const isPlainObject = (v) => v && typeof v === "object" && !Array.isArray(v);
const titleCase = (s = "") =>
  s.replace(/[_\-]+/g, " ")
   .replace(/\s+/g, " ")
   .trim()
   .replace(/\b\w/g, (m) => m.toUpperCase());

/** immutably set value at path: e.g. ["sites", 0, "name"] */
function setAtPath(obj, path, value) {
  if (!path.length) return value;
  const [head, ...tail] = path;
  const clone = Array.isArray(obj) ? obj.slice() : { ...(obj || {}) };
  clone[head] = setAtPath(clone[head], tail, value);
  return clone;
}

/** decide multiline string by key hint */
const isMultilineKey = (k = "") =>
  /notes|description|scope|assumptions|constraints|deliverables|questions|summary/i.test(k);

/** -------- leaf editors -------- */
function PrimitiveInput({ k, value, onChange }) {
  const type = typeof value;
  if (type === "boolean") {
    return (
      <label className="field" title={k}>
        <span className="label">{titleCase(k)}</span>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <input
            type="checkbox"
            className="input"
            checked={!!value}
            onChange={(e) => onChange(e.target.checked)}
            style={{ width:18, height:18 }}
          />
          <span className="hint">{String(value)}</span>
        </div>
      </label>
    );
  }
  if (type === "number") {
    return (
      <label className="field" title={k}>
        <span className="label">{titleCase(k)}</span>
        <input
          className="input"
          type="number"
          value={Number.isFinite(value) ? value : ""}
          onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
          placeholder="0"
        />
      </label>
    );
  }
  // fallback (string or null/undefined): show text/textarea
  const val = value == null ? "" : String(value);
  const multiline = isMultilineKey(k) || val.length > 120;
  return (
    <label className="field" title={k}>
      <span className="label">{titleCase(k)}</span>
      {multiline ? (
        <textarea
          className="textarea"
          value={val}
          onChange={(e) => onChange(e.target.value)}
          rows={6}
        />
      ) : (
        <input
          className="input"
          value={val}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </label>
  );
}

/** -------- recursive editors -------- */
function ArrayEditor({ k, value = [], path, onPatch }) {
  // decide primitive array vs array of objects
  const isObjects = value.some((v) => isPlainObject(v));
  const isPrims   = value.every((v) => !isPlainObject(v));

  // For primitive arrays: textarea with one per line
  if (isPrims) {
    const text = (value || []).map(v => (v ?? "")).join("\n");
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">[]</span>
            <h3 className="h3" style={{ margin: 0 }}>{titleCase(k)}</h3>
          </div>
          <p className="hint">One item per line</p>
        </div>
        <div className="panel-body">
          <textarea
            className="textarea"
            rows={Math.min(10, Math.max(4, value.length))}
            value={text}
            onChange={(e) => {
              const next = e.target.value
                .split(/\r?\n/)
                .map(s => s.trim())
                .filter(Boolean);
              onPatch(setAtPath, path, next);
            }}
          />
        </div>
      </div>
    );
  }

  // Array of objects: render each item as a nested panel
  const addEmpty = () => {
    const template = isObjects ? { ...(value[0] || {}) } : {};
    // if array is empty, default to { name:"", value:"" }                // generic fallback
    const empty = Object.keys(template).length ? Object.fromEntries(Object.keys(template).map(k => [k, ""])) : { name:"", value:"" };
    onPatch(setAtPath, path, [...(value || []), empty]);
  };
  const removeAt = (idx) => {
    const next = (value || []).filter((_, i) => i !== idx);
    onPatch(setAtPath, path, next);
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="section-title">
          <span className="icon">≡</span>
          <h3 className="h3" style={{ margin: 0 }}>{titleCase(k)}</h3>
        </div>
        <p className="hint">Add / remove items</p>
      </div>
      <div className="panel-body" style={{ display:"grid", gap:12 }}>
        {(value || []).map((item, idx) => (
          <div key={idx} className="panel" style={{ borderRadius: 14 }}>
            <div className="panel-header" style={{ paddingBottom: 6 }}>
              <div className="section-title">
                <span className="icon">{idx + 1}</span>
                <h4 className="h3" style={{ margin: 0 }}>Item {idx + 1}</h4>
              </div>
            </div>
            <div className="panel-body">
              {isPlainObject(item) ? (
                <ObjectEditor
                  k={`${k}[${idx}]`}
                  value={item}
                  path={[...path, idx]}
                  onPatch={onPatch}
                  nested
                />
              ) : (
                <PrimitiveInput
                  k={`${k}[${idx}]`}
                  value={item}
                  onChange={(v) => onPatch(setAtPath, [...path, idx], v)}
                />
              )}
              <div className="panel-actions" style={{ justifyContent:"flex-end", marginTop:8 }}>
                <button className="btn-secondary" type="button" onClick={() => removeAt(idx)}>Remove</button>
              </div>
            </div>
          </div>
        ))}
        <div className="panel-actions" style={{ justifyContent:"flex-end" }}>
          <button className="btn" type="button" onClick={addEmpty}>+ Add Item</button>
        </div>
      </div>
    </div>
  );
}

function ObjectEditor({ k, value = {}, path, onPatch, nested = false }) {
  const entries = Object.entries(value || {});
  const [prims, complex] = useMemo(() => {
    const prims = [];
    const comp  = [];
    for (const [key, val] of entries) {
      if (isPlainObject(val) || Array.isArray(val)) comp.push([key, val]);
      else prims.push([key, val]);
    }
    return [prims, comp];
  }, [entries]);

  return (
    <div className="panel">
      {!nested && (
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">🧩</span>
            <h3 className="h3" style={{ margin: 0 }}>{titleCase(k)}</h3>
          </div>
        </div>
      )}
      <div className="panel-body">
        {/* primitive fields */}
        {prims.length > 0 && (
          <div className="form-grid">
            {prims.map(([key, val]) => (
              <PrimitiveInput
                key={key}
                k={key}
                value={val}
                onChange={(v) => onPatch(setAtPath, [...path, key], v)}
              />
            ))}
          </div>
        )}

        {/* nested objects/arrays */}
        {complex.length > 0 && (
          <div style={{ display:"grid", gap:12, marginTop: prims.length ? 12 : 0 }}>
            {complex.map(([key, val]) =>
              Array.isArray(val) ? (
                <ArrayEditor
                  key={key}
                  k={key}
                  value={val}
                  path={[...path, key]}
                  onPatch={onPatch}
                />
              ) : (
                <ObjectEditor
                  key={key}
                  k={key}
                  value={val}
                  path={[...path, key]}
                  onPatch={onPatch}
                  nested
                />
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/** -------- main -------- */
export default function EditStep({ schema, onSchemaChange, onNext }) {
  const [jsonText, setJsonText] = useState(() => JSON.stringify(schema, null, 2));
  const [jsonErr, setJsonErr] = useState("");

  // keep JSON view in sync when schema changes elsewhere
  useEffect(() => {
    setJsonErr("");
    setJsonText(JSON.stringify(schema, null, 2));
  }, [schema]);

  // single patch function used by all nested editors
  const patch = (_set, path, value) => {
    const next = _set(schema, path, value);
    onSchemaChange(next);
  };

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
      {/* Full schema editor (recursive UI) */}
      <ObjectEditor
        k="Schema"
        value={schema || {}}
        path={[]}
        onPatch={patch}
      />

      {/* Full JSON (synced) */}
      <div className="panel">
        <div className="panel-header">
          <div className="section-title">
            <span className="icon">{"</>"}</span>
            <h3 className="h3" style={{ margin: 0 }}>Full Schema (JSON)</h3>
          </div>
          <p className="hint">Edit directly if easier. Changes here update the same schema above.</p>
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
          />
          <div className="panel-actions" style={{ justifyContent:"flex-end", marginTop:8 }}>
            <button className="btn" type="button" onClick={applyJson}>Apply JSON</button>
          </div>
        </div>
      </div>

      {/* Generate */}
      <div className="panel">
        <div className="panel-body" style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:12 }}>
          <span className="hint">Review/edit all fields above, then generate your LoE.</span>
          <button className="btn" onClick={onNext}>Generate</button>
        </div>
      </div>
    </div>
  );
}
