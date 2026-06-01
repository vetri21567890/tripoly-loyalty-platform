import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AdminAuthState {
  accessToken: string | null;
  setToken: (token: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAdminAuthStore = create<AdminAuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      setToken: (token) => set({ accessToken: token }),
      logout: () => {
        set({ accessToken: null });
        localStorage.removeItem("tripoly-admin-auth");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        sessionStorage.clear();
      },
      isAuthenticated: () => !!get().accessToken,
    }),
    { name: "tripoly-admin-auth" }
  )
);
