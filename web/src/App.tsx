import { Routes, Route, Navigate } from "react-router";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import KnowledgeBases from "./pages/KnowledgeBases";
import KbDetail from "./pages/KbDetail";
import WikiBrowser from "./pages/WikiBrowser";
import WikiDetail from "./pages/WikiDetail";
import Sources from "./pages/Sources";
import SubmitSource from "./pages/SubmitSource";
import SourceDetail from "./pages/SourceDetail";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="kb" element={<KnowledgeBases />} />
        <Route path="kb/:kbSlug" element={<KbDetail />} />
        <Route path="kb/:kbSlug/wiki" element={<WikiBrowser />} />
        <Route path="kb/:kbSlug/wiki/:slug" element={<WikiDetail />} />
        <Route path="kb/:kbSlug/sources" element={<Sources />} />
        <Route path="kb/:kbSlug/sources/submit" element={<SubmitSource />} />
        <Route path="kb/:kbSlug/sources/:sourceId" element={<SourceDetail />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
