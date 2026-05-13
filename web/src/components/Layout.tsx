import { Outlet } from "react-router";
import Sidebar from "./Sidebar";
import SearchBar from "./SearchBar";
import NotificationBadge from "./NotificationBadge";

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-gray-200 bg-white flex items-center px-6 shrink-0 gap-4">
          <SearchBar />
          <div className="ml-auto flex items-center">
            <NotificationBadge />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
