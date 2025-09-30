import { NavLink } from "react-router-dom";

export default function MegaMenu({ open, title, items, innerRef, onAnyClick }) {
  return (
    <div
      ref={innerRef}
      className={`mega ${open ? "open" : ""}`}
      role="menu"
      aria-label={title}
    >
      <div className="mega-inner">
        <div className="mega-title">{title}</div>
        <div className="mega-cols">
          {items.map((col, i) => (
            <div key={i} className="mega-col">
              <div className="mega-heading">{col.heading}</div>
              <ul className="mega-list">
                {col.links.map((l, idx) => (
                  <li key={idx}>
                    {l.disabled ? (
                      <span className="mega-link disabled" aria-disabled="true">
                        <span className="mega-label">{l.label}</span>
                        {l.meta && <span className="mega-meta">{l.meta}</span>}
                      </span>
                    ) : (
                      <NavLink
                        to={l.to}
                        className="mega-link"
                        role="menuitem"
                        onClick={onAnyClick}
                      >
                        <span className="mega-label">{l.label}</span>
                        {l.meta && <span className="mega-meta">{l.meta}</span>}
                      </NavLink>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
