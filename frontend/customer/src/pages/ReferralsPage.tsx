import { useQuery } from "@tanstack/react-query";
import { referralApi } from "../api/services";

export default function ReferralsPage() {
  const { data: me } = useQuery({ queryKey: ["referral"], queryFn: () => referralApi.me().then((r) => r.data.data) });
  const { data: status = [] } = useQuery({ queryKey: ["referral-status"], queryFn: () => referralApi.status().then((r) => r.data.data) });

  const summary = me?.status_summary ?? {};
  const pending = Number(summary.INVITED ?? summary.invited ?? 0);
  const qualified = Number(summary.QUALIFIED ?? summary.REWARD_ISSUED ?? summary.qualified ?? 0);

  const copyLink = () => {
    if (me?.referral_link) navigator.clipboard.writeText(me.referral_link);
  };

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">Referral Growth</p>
        <h2 className="page-title">Referrals</h2>
        <p className="page-subtitle">Share your Tripoly referral link and track pending and qualified referral rewards.</p>
      </section>

      <section className="panel-card">
        <p className="text-sm text-slate-500">Your referral code</p>
        <p className="mt-2 text-3xl font-bold tracking-wide text-emerald-600">{me?.referral_code ?? "-"}</p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <input readOnly value={me?.referral_link ?? ""} className="field flex-1" />
          <button onClick={copyLink} className="primary-button">
            Copy Link
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Metric label="Pending Referrals" value={pending} />
        <Metric label="Qualified Referrals" value={qualified} />
        <Metric label="Reward Events" value={status.length} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <h3 className="font-semibold text-slate-950">Referral Status</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {status.length ? (
            status.map((item, index) => (
              <div key={`${item.status}-${index}`} className="flex items-center justify-between p-4 text-sm">
                <span>Referral {index + 1}</span>
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium capitalize text-slate-700">{item.status.replace(/_/g, " ")}</span>
              </div>
            ))
          ) : (
            <p className="p-5 text-sm text-slate-500">No referrals tracked yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-emerald-600">{value}</p>
    </div>
  );
}
