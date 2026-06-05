import axios from "axios";
import { useAuthStore } from "../store/authStore";

export const apiBaseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
export const apiHealthURL = new URL("/health", apiBaseURL).toString();

export const api = axios.create({
  baseURL: apiBaseURL,
  headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "true" },
});

export function clearApiAuth() {
  delete api.defaults.headers.common.Authorization;
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    delete config.headers.Authorization;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = useAuthStore.getState().refreshToken;
      if (refresh && !error.config._retry) {
        error.config._retry = true;
        try {
          const { data } = await axios.post(
            `${apiBaseURL}/auth/token/refresh`,
            { refresh_token: refresh },
            { headers: { "ngrok-skip-browser-warning": "true" } },
          );
          const tokens = data.data;
          useAuthStore.getState().setTokens(tokens.access_token, tokens.refresh_token);
          error.config.headers.Authorization = `Bearer ${tokens.access_token}`;
          return api(error.config);
        } catch {
          useAuthStore.getState().logout();
          clearApiAuth();
        }
      }
    }
    return Promise.reject(error);
  }
);

export type ApiResponse<T> = { code: string; message: string; data: T };
