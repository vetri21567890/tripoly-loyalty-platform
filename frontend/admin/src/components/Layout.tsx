import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { clearApiAuth } from "../api/client";
import { useAdminAuthStore } from "../store/authStore";

const navGroups = [
  {
    label: "Core",
    items: [
      { to: "/", label: "Dashboard" },
      { to: "/customers", label: "Customers" },
    ],
  },
  {
    label: "Loyalty Program",
    items: [
      { to: "/loyalty/points-engine", label: "Points Engine" },
      { to: "/loyalty/rewards", label: "Rewards" },
      { to: "/loyalty/tiers", label: "Tiers / VIP" },
      { to: "/loyalty/missions", label: "Missions / Tasks" },
      { to: "/loyalty/referrals", label: "Referrals" },
      { to: "/loyalty/campaigns", label: "Campaigns" },
      { to: "/loyalty/wallet-rules", label: "Wallet Rules" },
      { to: "/loyalty/notifications", label: "Notifications" },
      { to: "/loyalty/program-settings", label: "Program Settings" },
      { to: "/loyalty/performance", label: "Performance" },
    ],
  },
  {
    label: "UGC & Reviews",
    items: [
      { to: "/ugc/moderation", label: "UGC Moderation" },
      { to: "/ugc/testimonials", label: "Testimonials" },
      { to: "/ugc/review-rewards", label: "Review Rewards" },
    ],
  },
  {
    label: "Travel Operations",
    items: [
      { to: "/travel/booking-webhooks", label: "Booking Webhooks" },
      { to: "/travel/partner-integrations", label: "Partner Integrations" },
      { to: "/travel/activity-logs", label: "Travel Activity Logs" },
    ],
  },
  {
    label: "Reports",
    items: [
      { to: "/reports/customer-analytics", label: "Customer Analytics" },
      { to: "/reports/wallet-analytics", label: "Wallet Analytics" },
      { to: "/reports/referral-analytics", label: "Referral Analytics" },
      { to: "/reports/campaign-analytics", label: "Campaign Analytics" },
      { to: "/reports/ugc-analytics", label: "UGC Analytics" },
      { to: "/reports/redemption-analytics", label: "Redemption Analytics" },
    ],
  },
  {
    label: "System",
    items: [
      { to: "/audit", label: "Audit Logs" },
      { to: "/settings", label: "Settings" },
    ],
  },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const logout = useAdminAuthStore((s) => s.logout);
  const handleLogout = () => {
    logout();
    clearApiAuth();
    navigate("/login", { replace: true });
  };

  const sidebar = (isMobile = false) => (
    <aside className={`${isMobile ? "flex h-full w-80 max-w-[88vw]" : "hidden lg:flex lg:min-h-screen lg:w-72"} flex-col bg-admin-primary text-white shadow-xl`}>
      <div className="border-b border-white/10 p-5">
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500 text-lg font-black text-white">T</div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Tripoly</p>
        <h1 className="mt-1 text-lg font-bold">Loyalty Operations</h1>
        <p className="mt-2 text-xs leading-5 text-emerald-50/70">Independent travel loyalty and retention command center.</p>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto p-3">
        {navGroups.map((group) => (
          <div key={group.label}>
            <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-100/50">{group.label}</p>
            <div className="space-y-1">
              {group.items.map((item) => {
                const active = location.pathname === item.to || (item.to !== "/" && location.pathname.startsWith(item.to));
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${
                      active ? "bg-emerald-500 text-white shadow-sm" : "text-emerald-50/80 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <button onClick={handleLogout} className="m-3 rounded-lg border border-white/10 px-3 py-2 text-left text-sm text-emerald-50/70 hover:bg-white/10 hover:text-white">
        Logout
      </button>
    </aside>
  );

  return (
    <div className="min-h-screen bg-admin-surface lg:flex">
      {sidebar()}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-slate-950/50"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative h-full">{sidebar(true)}</div>
        </div>
      )}
      <main className="min-w-0 flex-1">
        <div className="sticky top-0 z-30 border-b border-slate-200 bg-white px-4 py-3 shadow-sm sm:px-6 lg:static lg:px-6 lg:py-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label="Open menu"
              onClick={() => setMobileMenuOpen(true)}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-xl text-slate-700 lg:hidden"
            >
              ≡
            </button>
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-600 sm:text-xs">Admin Workspace</p>
              <h2 className="mt-1 truncate text-base font-bold text-slate-950 sm:text-xl">Travel Loyalty Control Plane</h2>
            </div>
          </div>
        </div>
        <div className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
