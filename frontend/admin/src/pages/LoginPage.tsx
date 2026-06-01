import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api, clearApiAuth } from "../api/client";
import { useAdminAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@tripoly.app");
  const [password, setPassword] = useState("Admin@12345");
  const [error, setError] = useState("");
  const setToken = useAdminAuthStore((s) => s.setToken);
  const accessToken = useAdminAuthStore((s) => s.accessToken);
  const navigate = useNavigate();

  if (accessToken) {
    return <Navigate to="/" replace />;
  }

  const login = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    clearApiAuth();
    try {
      const { data } = await api.post("/admin/auth/login", { email: email.trim(), password });
      setToken(data.data.access_token);
      navigate("/", { replace: true });
    } catch {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-admin-primary">
      <form onSubmit={login} className="bg-white p-8 rounded-xl shadow w-full max-w-md space-y-4">
        <h1 className="text-xl font-bold">Admin Login</h1>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border rounded px-4 py-2" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full border rounded px-4 py-2" />
        <button type="submit" className="w-full bg-admin-accent text-white py-2 rounded">Login</button>
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </form>
    </div>
  );
}
