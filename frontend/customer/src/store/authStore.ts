import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      logout: () => {
        set({ accessToken: null, refreshToken: null });
        localStorage.removeItem("tripoly-auth");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        sessionStorage.clear();
      },
      isAuthenticated: () => !!get().accessToken,
    }),
    { name: "tripoly-auth" }
  )
);
