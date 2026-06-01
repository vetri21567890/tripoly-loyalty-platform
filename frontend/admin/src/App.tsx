import { Navigate, Route, Routes } from "react-router-dom";
import { useAdminAuthStore } from "./store/authStore";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import UgcModerationPage from "./pages/UgcModerationPage";
import RewardsManagePage from "./pages/RewardsManagePage";
import EarningRulesPage from "./pages/EarningRulesPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import AdminDataPage from "./pages/AdminDataPage";
import AdminSummaryPage from "./pages/AdminSummaryPage";
import TierManagementPage from "./pages/TierManagementPage";
import WalletRulesPage from "./pages/WalletRulesPage";
import CampaignManagementPage from "./pages/CampaignManagementPage";
import CustomerManagementPage from "./pages/CustomerManagementPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAdminAuthStore((s) => s.accessToken);
  return accessToken ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="customers" element={<CustomerManagementPage />} />
        <Route
          path="loyalty/points-engine"
          element={
            <AdminSummaryPage
              title="Points Engine"
              endpoint="/admin/points-engine"
              description="Manage travel booking bonuses, UGC reward rules, referral rewards, birthday bonuses, campaign rewards, and mission rewards."
            />
          }
        />
        <Route path="loyalty/rewards" element={<RewardsManagePage />} />
        <Route path="loyalty/tiers" element={<TierManagementPage />} />
        <Route path="loyalty/campaigns" element={<CampaignManagementPage />} />
        <Route
          path="loyalty/missions"
          element={
            <AdminDataPage
              title="Mission Management"
              endpoint="/admin/missions"
              columns={[
                { key: "code", label: "Code" },
                { key: "title", label: "Title" },
                { key: "coins_awarded", label: "Coins" },
                { key: "is_one_time", label: "One Time" },
                { key: "status", label: "Status" },
              ]}
            />
          }
        />
        <Route
          path="loyalty/referrals"
          element={
            <AdminDataPage
              title="Referral Management"
              endpoint="/admin/referrals"
              columns={[
                { key: "referred_email", label: "Referred Email" },
                { key: "referred_phone", label: "Referred Phone" },
                { key: "referral_source", label: "Source" },
                { key: "status", label: "Status" },
                { key: "qualified_at", label: "Qualified" },
                { key: "reward_issued_at", label: "Reward Issued" },
              ]}
            />
          }
        />
        <Route path="loyalty/wallet-rules" element={<WalletRulesPage />} />
        <Route path="loyalty/earning-rules" element={<EarningRulesPage />} />
        <Route
          path="loyalty/notifications"
          element={
            <AdminDataPage
              title="Loyalty Notifications"
              endpoint="/admin/notifications"
              columns={[
                { key: "customer_id", label: "Customer" },
                { key: "type", label: "Type" },
                { key: "title", label: "Title" },
                { key: "read_at", label: "Read" },
                { key: "created_at", label: "Created" },
              ]}
            />
          }
        />
        <Route
          path="loyalty/program-settings"
          element={
            <AdminSummaryPage
              title="Program Settings"
              endpoint="/admin/program-settings"
              description="Manage coin expiry policy, referral amounts, UGC approval requirements, campaign eligibility, redemption limits, and wallet rules."
            />
          }
        />
        <Route
          path="loyalty/performance"
          element={
            <AdminSummaryPage
              title="Performance"
              endpoint="/admin/performance"
              description="Track active customers, coins issued and redeemed, referral conversions, UGC submissions, reward redemptions, campaign participation, and repeat engagement."
            />
          }
        />
        <Route path="ugc/moderation" element={<UgcModerationPage />} />
        <Route
          path="ugc/testimonials"
          element={
            <AdminDataPage
              title="Testimonials"
              endpoint="/admin/ugc/attempts"
              columns={[
                { key: "ugc_attempt_id", label: "Attempt" },
                { key: "customer_id", label: "Customer" },
                { key: "ugc_type", label: "Type" },
                { key: "status", label: "Status" },
                { key: "rejection_reason", label: "Rejection Reason" },
              ]}
            />
          }
        />
        <Route path="ugc/review-rewards" element={<EarningRulesPage />} />
        <Route
          path="travel/booking-webhooks"
          element={
            <AdminDataPage
              title="Booking Webhooks"
              endpoint="/admin/travel/booking-webhooks"
              columns={[
                { key: "source_system", label: "Source" },
                { key: "source_booking_id", label: "Booking ID" },
                { key: "customer_id", label: "Customer" },
                { key: "booking_value_inr", label: "Value INR" },
                { key: "coins_awarded", label: "Coins" },
                { key: "confirmed_at", label: "Confirmed" },
              ]}
            />
          }
        />
        <Route
          path="travel/partner-integrations"
          element={
            <AdminDataPage
              title="Partner Integrations"
              endpoint="/admin/travel/partner-integrations"
              columns={[
                { key: "integration", label: "Integration" },
                { key: "connection_model", label: "Connection Model" },
                { key: "status", label: "Status" },
                { key: "events_received", label: "Events" },
              ]}
            />
          }
        />
        <Route
          path="travel/activity-logs"
          element={
            <AdminDataPage
              title="Travel Activity Logs"
              endpoint="/admin/travel/activity-logs"
              columns={[
                { key: "activity_type", label: "Activity" },
                { key: "source_system", label: "Source" },
                { key: "customer_id", label: "Customer" },
                { key: "coins_awarded", label: "Coins" },
                { key: "created_at", label: "Created" },
              ]}
            />
          }
        />
        {["customer-analytics", "wallet-analytics", "referral-analytics", "campaign-analytics", "ugc-analytics", "redemption-analytics"].map((report) => (
          <Route
            key={report}
            path={`reports/${report}`}
            element={
              <AdminSummaryPage
                title={report.replace(/-/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())}
                endpoint={`/admin/reports/${report}`}
                description="Report view for Tripoly loyalty operations, based on first-party platform data and connected travel webhooks."
              />
            }
          />
        ))}
        <Route path="audit" element={<AuditLogsPage />} />
        <Route
          path="settings"
          element={
            <AdminSummaryPage
              title="Settings"
              endpoint="/admin/program-settings"
              description="Operational settings for the independent Tripoly loyalty platform. External tools connect through API/webhook surfaces only."
            />
          }
        />
        <Route path="ugc" element={<Navigate to="/ugc/moderation" replace />} />
        <Route path="rewards" element={<Navigate to="/loyalty/rewards" replace />} />
        <Route path="campaigns" element={<Navigate to="/loyalty/campaigns" replace />} />
        <Route path="missions" element={<Navigate to="/loyalty/missions" replace />} />
        <Route path="referrals" element={<Navigate to="/loyalty/referrals" replace />} />
        <Route path="wallet" element={<Navigate to="/loyalty/wallet-rules" replace />} />
        <Route path="earning-rules" element={<Navigate to="/loyalty/points-engine" replace />} />
        <Route path="notifications" element={<Navigate to="/loyalty/notifications" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
