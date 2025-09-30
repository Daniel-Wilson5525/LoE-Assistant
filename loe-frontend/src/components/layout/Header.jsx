import React, { useState } from "react";
import { Link, NavLink } from "react-router-dom";

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="topnav">
      <div className="topnav-inner">
        <Link to="/" className="brand">
          <span className="brand-dot" /> WWT LOE Assistant
        </Link>

        <nav className="nav">
          <NavLink to="/" end className="nav-link">
            Home
          </NavLink>

          {/* Hover parent */}
          <div
            className="nav-link has-menu"
            onMouseEnter={() => setOpen(true)}
            onMouseLeave={() => setOpen(false)}
          >
            LOE Assistants
            <span className="caret">▾</span>

            {/* Mega menu */}
            <div className={`mega ${open ? "open" : ""}`}>
              <div className="mega-col">
                <div className="mega-title">Currently available</div>
                <Link className="mega-item" to="/assistants/rack-stack">
                  Rack &amp; Stack
                </Link>
              </div>

              <div className="mega-col">
                <div className="mega-title">Coming soon</div>
                <div className="mega-item disabled">Wireless Install</div>
                <div className="mega-item disabled">Switch Install</div>
                <div className="mega-item disabled">Device Relocation</div>
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
