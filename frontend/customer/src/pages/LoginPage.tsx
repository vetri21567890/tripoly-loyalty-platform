import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { apiHealthURL, clearApiAuth } from "../api/client";
import { authApi } from "../api/services";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [warmingApi, setWarmingApi] = useState(true);
  const setTokens = useAuthStore((s) => s.setTokens);
  const accessToken = useAuthStore((s) => s.accessToken);
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

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    clearApiAuth();
    try {
      const { data } =
        mode === "signup"
          ? await authApi.signup(email, password, firstName || undefined, lastName || undefined)
          : await authApi.signin(email, password);
      setTokens(data.data.access_token, data.data.refresh_token);
      navigate("/", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const message =
          (err.response?.data?.detail?.message as string | undefined) ||
          (err.response?.data?.message as string | undefined) ||
          (mode === "signup" ? "Signup failed" : "Login failed");
        setError(message);
      } else {
        setError(mode === "signup" ? "Signup failed" : "Login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-tripoly-dark p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-xl">
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-500 text-xl font-black text-white">T</div>
        <p className="eyebrow">Customer Portal</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-950">Tripoly Loyalty</h1>
        <p className="text-slate-500 mb-6">
          {warmingApi ? "Connecting to the live server..." : mode === "signup" ? "Create your account" : "Sign in with email"}
        </p>
        <form onSubmit={submit} className="space-y-4">
          {mode === "signup" && (
            <>
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-slate-700">First name</span>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Enter your first name"
                  autoComplete="given-name"
                  className="field h-12"
                />
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-slate-700">Last name</span>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Enter your last name"
                  autoComplete="family-name"
                  className="field h-12"
                />
              </label>
            </>
          )}
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-slate-700">Email address</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              className="field h-12"
              required
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-slate-700">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "signup" ? "Create a password, minimum 8 characters" : "Enter your password"}
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              className="field h-12"
              minLength={8}
              required
            />
          </label>
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center rounded-lg bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? (mode === "signup" ? "Creating account..." : "Signing in...") : mode === "signup" ? "Sign Up" : "Sign In"}
          </button>
          {loading && (
            <p className="text-center text-xs text-slate-500">
              Free hosting may take a short moment to wake up after inactivity.
            </p>
          )}
          <button
            type="button"
            onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
            className="text-sm text-slate-500 w-full"
          >
            {mode === "signin" ? "New user? Create account" : "Already have an account? Sign in"}
          </button>
        </form>
        {error && <p className="text-red-600 text-sm mt-4">{error}</p>}
      </div>
    </div>
  );
}
