import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { clearApiAuth } from "../api/client";
import { notificationsApi } from "../api/services";
import { useAuthStore } from "../store/authStore";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/wallet", label: "Wallet" },
  { to: "/rewards", label: "Rewards" },
  { to: "/referrals", label: "Referrals" },
  { to: "/ugc", label: "UGC Uploads" },
  { to: "/missions", label: "Missions" },
  { to: "/campaigns", label: "Campaigns" },
  { to: "/profile", label: "Profile" },
  { to: "/notifications", label: "Notifications" },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const { data: unread } = useQuery({
    queryKey: ["unread"],
    queryFn: () => notificationsApi.unreadCount().then((r) => r.data.data.unread_count),
  });
  const handleLogout = () => {
    logout();
    clearApiAuth();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-tripoly-surface lg:flex">
      <aside className="flex w-full flex-col bg-tripoly-dark text-white shadow-xl lg:min-h-screen lg:w-72">
        <div className="border-b border-white/10 p-5">
          <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500 text-lg font-black text-white">T</div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Tripoly</p>
          <h1 className="mt-1 text-lg font-bold">Loyalty Portal</h1>
          <p className="mt-2 text-xs leading-5 text-emerald-50/70">Travel rewards, missions, referrals, and UGC in one place.</p>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`block rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                location.pathname === item.to ? "bg-emerald-500 text-white shadow-sm" : "text-emerald-50/80 hover:bg-white/10 hover:text-white"
              }`}
            >
              {item.label}
              {item.to === "/notifications" && unread ? ` (${unread})` : ""}
            </Link>
          ))}
        </nav>
        <button onClick={handleLogout} className="m-3 rounded-lg border border-white/10 px-3 py-2 text-left text-sm text-emerald-50/70 hover:bg-white/10 hover:text-white">
          Logout
        </button>
      </aside>
      <main className="min-w-0 flex-1 overflow-auto">
        <div className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Independent Travel Loyalty Platform</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">Customer Experience</h2>
        </div>
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
