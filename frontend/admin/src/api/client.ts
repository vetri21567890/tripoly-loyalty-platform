import axios from "axios";
import { useAdminAuthStore } from "../store/authStore";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL,
  headers: { "ngrok-skip-browser-warning": "true" },
});

export function clearApiAuth() {
  delete api.defaults.headers.common.Authorization;
}

api.interceptors.request.use((config) => {
  const token = useAdminAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    delete config.headers.Authorization;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAdminAuthStore.getState().logout();
      clearApiAuth();
    }
    return Promise.reject(error);
  }
);

export type ApiResponse<T> = { code: string; message: string; data: T };
