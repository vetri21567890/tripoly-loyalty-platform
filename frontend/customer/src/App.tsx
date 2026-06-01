import { Navigate, Route, Routes } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import WalletPage from "./pages/WalletPage";
import RewardsPage from "./pages/RewardsPage";
import ReferralsPage from "./pages/ReferralsPage";
import ProfilePage from "./pages/ProfilePage";
import UgcPage from "./pages/UgcPage";
import MissionsPage from "./pages/MissionsPage";
import CampaignsPage from "./pages/CampaignsPage";
import NotificationsPage from "./pages/NotificationsPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken);
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
        <Route path="wallet" element={<WalletPage />} />
        <Route path="rewards" element={<RewardsPage />} />
        <Route path="referrals" element={<ReferralsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="ugc" element={<UgcPage />} />
        <Route path="missions" element={<MissionsPage />} />
        <Route path="campaigns" element={<CampaignsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
