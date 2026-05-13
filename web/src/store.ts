import { create } from "zustand";

interface AppState {
  currentKbSlug: string | null;
  sidebarOpen: boolean;
  setCurrentKbSlug: (slug: string | null) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentKbSlug: null,
  sidebarOpen: true,
  setCurrentKbSlug: (slug) => set({ currentKbSlug: slug }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
