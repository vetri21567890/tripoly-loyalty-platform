import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api, apiHealthURL, clearApiAuth } from "../api/client";
import { useAdminAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@tripoly.app");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [warmingApi, setWarmingApi] = useState(true);
  const setToken = useAdminAuthStore((s) => s.setToken);
  const accessToken = useAdminAuthStore((s) => s.accessToken);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    fetch(apiHealthURL, { headers: { "ngrok-skip-browser-warning": "true" } })
      .catch(() => undefined)
      .finally(() => {
        if (mounted) setWarmingApi(false);
      });
    const fallback = window.setTimeout(() => {
      if (mounted) setWarmingApi(false);
    }, 10000);
    return () => {
      mounted = false;
      window.clearTimeout(fallback);
    };
  }, []);

  if (accessToken) {
    return <Navigate to="/" replace />;
  }

  const login = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    clearApiAuth();
    try {
      const { data } = await api.post("/admin/auth/login", { email: email.trim(), password });
      setToken(data.data.access_token);
      navigate("/", { replace: true });
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-admin-primary">
      <form onSubmit={login} className="bg-white p-8 rounded-xl shadow w-full max-w-md space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-admin-accent">Admin Portal</p>
          <h1 className="mt-2 text-2xl font-bold text-slate-950">Sign in to Tripoly</h1>
          <p className="mt-1 text-sm text-slate-500">
            {warmingApi ? "Connecting to the live server..." : "Use your admin email and password."}
          </p>
        </div>
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-slate-700">Email address</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@tripoly.app"
            autoComplete="email"
            className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-950 outline-none focus:border-admin-accent focus:ring-2 focus:ring-emerald-100"
            required
          />
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-slate-700">Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter admin password"
            autoComplete="current-password"
            className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-950 outline-none focus:border-admin-accent focus:ring-2 focus:ring-emerald-100"
            required
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center rounded-lg bg-admin-accent py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
        {loading && (
          <p className="text-center text-xs text-slate-500">
            Free hosting may take a short moment to wake up after inactivity.
          </p>
        )}
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </form>
    </div>
  );
}
