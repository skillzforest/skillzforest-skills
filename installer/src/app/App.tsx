import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppDataProvider } from "../store/AppContext";
import { Layout } from "../components/Layout";
import { Welcome } from "../pages/Welcome";
import { Home } from "../pages/Home";
import { MySkills } from "../pages/MySkills";
import { SkillDetails } from "../pages/SkillDetails";
import { PackDetails } from "../pages/PackDetails";
import { Updates } from "../pages/Updates";
import { Settings } from "../pages/Settings";
import { useDeepLinks } from "./useDeepLinks";

// HashRouter (not BrowserRouter) because the production build is loaded from
// a local `tauri://` asset root, not a real HTTP server with path routing.
function Router() {
  useDeepLinks();
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route element={<Layout />}>
        <Route path="/home" element={<Home />} />
        <Route path="/my-skills" element={<MySkills />} />
        <Route path="/skills/:skillId" element={<SkillDetails />} />
        <Route path="/packs/:packId" element={<PackDetails />} />
        <Route path="/updates" element={<Updates />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AppDataProvider>
      <HashRouter>
        <Router />
      </HashRouter>
    </AppDataProvider>
  );
}
