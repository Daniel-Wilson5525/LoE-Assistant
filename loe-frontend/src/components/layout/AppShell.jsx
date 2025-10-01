import React from "react";

export default function AppShell({ title, rightSlot, children }) {
  return (
    <div className="min-h-screen relative">
      {/* soft gradient background */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_left,rgba(59,130,246,0.10),transparent_40%),radial-gradient(ellipse_at_bottom_right,rgba(99,102,241,0.10),transparent_45%)]" />
      <header className="sticky top-0 z-40 backdrop-blur bg-white/70 border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
          <div className="flex items-center gap-2">{rightSlot}</div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
