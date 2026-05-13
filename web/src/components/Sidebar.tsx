import { Link, useParams, useLocation } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "../store";
import { api } from "../api/client";
import type { KnowledgeBase } from "../types";

export default function Sidebar() {
  const { kbSlug } = useParams();
  const location = useLocation();
  const { sidebarOpen, setCurrentKbSlug } = useAppStore();

  const { data: knowledgeBases = [] } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  const currentKb = knowledgeBases.find((kb) => kb.slug === kbSlug);

  if (kbSlug && currentKb) {
    setCurrentKbSlug(kbSlug);
  }

  if (!sidebarOpen) {
    return null;
  }

  const kbNavItems = kbSlug
    ? [
        { to: `/kb/${kbSlug}`, label: "概览", icon: "📊" },
        { to: `/kb/${kbSlug}/wiki`, label: "Wiki", icon: "📖" },
        { to: `/kb/${kbSlug}/sources`, label: "来源", icon: "📄" },
      ]
    : [];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <Link to="/" className="text-lg font-bold text-gray-800">
          KnowablePlat
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto p-4 space-y-6">
        <div>
          <Link
            to="/"
            className={`block px-3 py-2 rounded-md text-sm ${
              location.pathname === "/" ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            🏠 仪表盘
          </Link>
          <Link
            to="/kb"
            className={`block px-3 py-2 rounded-md text-sm ${
              location.pathname === "/kb" ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            📚 知识库管理
          </Link>
        </div>

        {kbSlug && (
          <div>
            <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">
              {currentKb?.name ?? kbSlug}
            </div>
            {kbNavItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`block px-3 py-2 rounded-md text-sm ${
                  location.pathname === item.to
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                {item.icon} {item.label}
              </Link>
            ))}
          </div>
        )}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <select
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white"
          value={kbSlug ?? ""}
          onChange={(e) => {
            if (e.target.value) {
              window.location.href = `/kb/${e.target.value}`;
            }
          }}
        >
          <option value="">选择知识库...</option>
          {knowledgeBases.map((kb) => (
            <option key={kb.id} value={kb.slug}>
              {kb.name}
            </option>
          ))}
        </select>
      </div>
    </aside>
  );
}
