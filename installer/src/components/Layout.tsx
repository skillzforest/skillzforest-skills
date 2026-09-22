import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/home", label: "Home" },
  { to: "/my-skills", label: "My Skills" },
  { to: "/updates", label: "Updates" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="sidebar-brand">SkillzForest</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="main-content">
        <Outlet />
      </div>
    </div>
  );
}
