import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

/** click outside helper */
function useClickOutside(ref, onOutside) {
  useEffect(() => {
    function handler(e) {
      if (!ref.current) return;
      if (!ref.current.contains(e.target)) onOutside?.();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onOutside, ref]);
}

/** sticky header w/ scroll shadow + mode switch dropdown */
export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const { pathname } = useLocation();

  // close menu on route change
  useEffect(() => setMenuOpen(false), [pathname]);

  // shadow when scrolling
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 2);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useClickOutside(menuRef, () => setMenuOpen(false));

  const assistants = [
    { label: "Rack & Stack", to: "/assistants/rack-stack/1", desc: "Paste → Edit → Generate" },
    // { label: "General LOE", to: "/assistants/default/1", desc: "Plain-language effort" }, // add when ready
  ];

  return (
    <header className={`topnav ${scrolled ? "scrolled" : ""}`}>
      <div className="topnav-inner">
        {/* Brand */}
        <Link to="/" className="brand" aria-label="WWT LOE Assistant Home">
          <span className="brand-dot" />
          WWT LOE Assistant
        </Link>

        {/* Right nav */}
        <nav className="nav" aria-label="Primary">
          <NavLink
            to="/"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            end
          >
            Home
          </NavLink>

          {/* Assistants dropdown */}
          <div className="nav-link has-menu" ref={menuRef}>
            <button
              type="button"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
              style={{ all: "unset", cursor: "pointer" }}
            >
              LOE Assistants <span className="caret">▾</span>
            </button>

            <div className={`mega ${menuOpen ? "open" : ""}`} role="menu" aria-label="LOE Assistants">
              <div className="mega-col">
                <div className="mega-title">Available</div>
                {assistants.map((a) => (
                  <NavLink
                    key={a.to}
                    to={a.to}
                    role="menuitem"
                    className={({ isActive }) =>
                      `mega-item ${isActive ? "active" : ""}`
                    }
                  >
                    <div style={{ fontWeight: 600 }}>{a.label}</div>
                    <div className="small" style={{ color: "var(--muted)" }}>
                      {a.desc}
                    </div>
                  </NavLink>
                ))}
              </div>

              <div className="mega-col">
                <div className="mega-title">Coming soon</div>
                <span className="mega-item disabled">General LOE</span>
                <span className="mega-item disabled">Wave Plan</span>
              </div>
            </div>
          </div>

          <a
            className="nav-link"
            href="https://www.wwt.com"
            target="_blank"
            rel="noreferrer"
          >
            WWT.com
          </a>
        </nav>
      </div>
    </header>
  );
}
