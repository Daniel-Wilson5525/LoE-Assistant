export const API_BASE = "http://127.0.0.1:5050";

export async function ingestLoE(text, loeType = "rack_stack") {
  const res = await fetch("http://127.0.0.1:5050/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, loe_type: loeType })
  });
  if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
  return res.json(); // { schema: {...} }
}

export async function generateLoE(schema) {
  const res = await fetch("http://127.0.0.1:5050/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema })
  });
  if (!res.ok) throw new Error(`Generate failed: ${res.status}`);
  return res.json(); // { summary, tasks, open_questions }
}
