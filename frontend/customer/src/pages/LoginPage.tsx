import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { clearApiAuth } from "../api/client";
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
  const setTokens = useAuthStore((s) => s.setTokens);
  const accessToken = useAuthStore((s) => s.accessToken);
  const navigate = useNavigate();

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
        <p className="text-slate-500 mb-6">{mode === "signup" ? "Create your account" : "Sign in with email"}</p>
        <form onSubmit={submit} className="space-y-4">
          {mode === "signup" && (
            <>
              <input
                type="text"
                aria-label="First name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="field h-12"
              />
              <input
                type="text"
                aria-label="Last name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="field h-12"
              />
            </>
          )}
          <input
            type="email"
            aria-label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="field h-12"
            required
          />
          <input
            type="password"
            aria-label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="field h-12"
            minLength={8}
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {loading ? "Please wait..." : mode === "signup" ? "Sign Up" : "Sign In"}
          </button>
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
