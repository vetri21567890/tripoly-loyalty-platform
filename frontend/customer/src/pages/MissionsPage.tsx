import { useQuery } from "@tanstack/react-query";
import { missionsApi } from "../api/services";

export default function MissionsPage() {
  const { data: available } = useQuery({ queryKey: ["missions"], queryFn: () => missionsApi.available().then((r) => r.data.data) });
  const { data: progress } = useQuery({ queryKey: ["mission-progress"], queryFn: () => missionsApi.progress().then((r) => r.data.data) });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">Travel Engagement</p>
        <h2 className="page-title">Missions</h2>
        <p className="page-subtitle">Complete profile, referral, review, photo, and campaign tasks to earn Travel Coins.</p>
      </section>
      <div className="grid md:grid-cols-2 gap-6">
        <section className="panel-card">
          <h3 className="font-semibold mb-3">Available</h3>
          {available?.map((m) => (
            <div key={m.mission_code} className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-4 mb-2">
              <p className="font-medium">{m.title}</p>
              <p className="text-emerald-700 text-sm font-semibold">+{m.coins_awarded} Coins</p>
            </div>
          ))}
        </section>
        <section className="panel-card">
          <h3 className="font-semibold mb-3">Your Progress</h3>
          {progress?.map((m) => (
            <div key={m.mission_code} className="rounded-lg border border-slate-200 bg-slate-50 p-4 mb-2 flex justify-between">
              <span>{m.mission_code}</span>
              <span className="status-pill capitalize">{m.status}</span>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
