import { NavLink } from "react-router-dom";
import MegaMenu from "./MegaMenu.jsx";
import { useState, useRef } from "react";

const LOE_ASSISTANTS = [
  { key: "rack-stack", label: "Rack & Stack", path: "/assistants/rack-stack", description: "Appliances, APs, brackets & BOM" },
  // future: add more assistants here
];

export default function Header() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  return (
    <header className="site-header">
      <div className="header-inner">
        <NavLink to="/" className="brand">
          <span className="brand-mark">WWT</span>
          <span className="brand-name">LOE</span>
        </NavLink>

        <nav className="nav">
          <div
            className="nav-item has-mega"
            onMouseEnter={() => setOpen(true)}
            onMouseLeave={() => setOpen(false)}
          >
            <button
              className="nav-link"
              aria-haspopup="true"
              aria-expanded={open}
              onFocus={() => setOpen(true)}
              onBlur={(e) => {
                // close only if focus truly left the whole menu
                if (!menuRef.current?.contains(e.relatedTarget)) setOpen(false);
              }}
            >
              LOE Assistants
              <span className={`chev ${open ? "up" : ""}`}>▾</span>
            </button>

            <MegaMenu
              innerRef={menuRef}
              open={open}
              title="Choose an assistant"
              items={[
                {
                  heading: "Available now",
                  links: LOE_ASSISTANTS.map(a => ({
                    label: a.label,
                    to: a.path,
                    meta: a.description
                  })),
                },
                {
                  heading: "Coming soon",
                  links: [
                    { label: "Wireless Install", to: "#", disabled: true, meta: "AP placement, waves & validation" },
                    { label: "Device Relocation", to: "#", disabled: true, meta: "Move, decommission, re-rack" },
                  ],
                },
              ]}
              onAnyClick={() => setOpen(false)}
            />
          </div>

          <NavLink to="/" className="nav-link">Docs</NavLink>
          <NavLink to="/" className="nav-link">Support</NavLink>
        </nav>
      </div>
    </header>
  );
}
