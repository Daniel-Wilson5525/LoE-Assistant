import React from "react";
import { useState, useEffect } from "react";

// TODO: Replace these with your real editors
function JsonPreview({ schema, onChange }) {
  const [val, setVal] = useState(JSON.stringify(schema, null, 2));
  useEffect(() => { setVal(JSON.stringify(schema, null, 2)); }, [schema]);
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <h4 className="font-semibold mb-2">Quick JSON (optional)</h4>
        <textarea
          className="w-full min-h-[320px] border border-slate-300 rounded-lg p-3 font-mono text-sm"
          value={val}
          onChange={(e) => setVal(e.target.value)}
        />
        <div className="mt-2">
          <button
            className="px-3 py-1.5 rounded bg-slate-800 text-white"
            onClick={() => {
              try { onChange(JSON.parse(val)); }
              catch { alert("Invalid JSON"); }
            }}
          >
            Apply JSON
          </button>
        </div>
      </div>
      <div>
        <h4 className="font-semibold mb-2">Preview</h4>
        <pre className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm overflow-auto">
{JSON.stringify(schema, null, 2)}
        </pre>
      </div>
    </div>
  );
}

export default function EditStep({ schema, onSchemaChange, onNext }) {
  return (
    <div className="max-w-5xl">
      <p className="text-slate-600 mb-4">
        Review the extracted fields below. (Plug your Sites/BOM/WavePlan editors here.)
      </p>

      {/* Drop-in area for your editors: */}
      {/* <SitesEditor value={schema.sites} onChange={(v)=>onSchemaChange({...schema, sites: v})} /> */}
      {/* <BOMEditor   value={schema.bom}   onChange={(v)=>onSchemaChange({...schema, bom: v})}   /> */}
      {/* <WavePlanEditor value={schema.wave_plan} onChange={(v)=>onSchemaChange({...schema, wave_plan: v})} /> */}
      
      <JsonPreview schema={schema} onChange={onSchemaChange} />

      <div className="mt-6">
        <button
          className="px-4 py-2 rounded-lg bg-blue-600 text-white"
          onClick={onNext}
        >
          Generate
        </button>
      </div>
    </div>
  );
}
