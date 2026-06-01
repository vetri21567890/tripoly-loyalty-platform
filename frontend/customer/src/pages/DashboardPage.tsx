import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { campaignsApi, missionsApi, referralApi, rewardsApi, tierApi, walletApi } from "../api/services";

export default function DashboardPage() {
  const { data: wallet } = useQuery({
    queryKey: ["wallet-balance"],
    queryFn: () => walletApi.balance().then((r) => r.data.data),
  });
  const { data: tier } = useQuery({
    queryKey: ["tier"],
    queryFn: () => tierApi.current().then((r) => r.data.data),
  });
  const { data: referral } = useQuery({
    queryKey: ["referral-me"],
    queryFn: () => referralApi.me().then((r) => r.data.data),
  });
  const { data: expiring } = useQuery({
    queryKey: ["expiring-soon"],
    queryFn: () => walletApi.expiringSoon(30, 5).then((r) => r.data.data),
  });
  const { data: txs } = useQuery({
    queryKey: ["recent-transactions"],
    queryFn: () => walletApi.transactions(5).then((r) => r.data.data),
  });
  const { data: rewards } = useQuery({
    queryKey: ["recent-rewards"],
    queryFn: () => rewardsApi.history(5).then((r) => r.data.data),
  });
  const { data: campaigns } = useQuery({
    queryKey: ["campaigns-active"],
    queryFn: () => campaignsApi.list().then((r) => r.data.data),
  });
  const { data: missionProgress } = useQuery({
    queryKey: ["missions-progress"],
    queryFn: () => missionsApi.progress().then((r) => r.data.data),
  });

  const completedCount = missionProgress?.filter((m: any) => m.status === "COMPLETED").length ?? 0;
  const inProgressCount = missionProgress?.filter((m: any) => m.status !== "COMPLETED").length ?? 0;
  const referralCount = Object.values(referral?.status_summary ?? {}).reduce((sum: number, count: any) => sum + Number(count), 0);

  return (
    <div className="page-shell">
      <section className="page-hero">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="eyebrow">Travel Retention Dashboard</p>
            <h2 className="page-title">Your Tripoly loyalty activity</h2>
            <p className="page-subtitle">
              Track coins, tier progress, referral impact, travel campaigns, missions, and submitted travel content.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <MiniMetric label="Campaigns" value={campaigns?.length ?? 0} />
            <MiniMetric label="Missions" value={completedCount + inProgressCount} />
            <MiniMetric label="Referrals" value={referralCount} />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card
          title="Travel Coins Balance"
          value={wallet?.available_coins ?? 0}
          subtitle={wallet ? `Approx value: ₹${wallet.approx_redemption_value_inr}` : undefined}
        />
        <Card title="Your Tier" value={tier?.tier_name ?? "-"} subtitle={tier?.tier_code} />
        <Card title="Referral Code" value={referral?.referral_code ?? "-"} subtitle="Share with friends" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Panel title="Conversion Rule">
          <p className="text-3xl font-bold text-emerald-600">{wallet?.conversion_rule ?? "10 Travel Coins = ₹1"}</p>
          <p className="mt-2 text-sm text-slate-500">Lifetime earned: {wallet?.lifetime_coins_earned ?? 0} Travel Coins</p>
          <p className="text-sm text-slate-500">Redeemed: {wallet?.redeemed_coins_to_date ?? 0} Travel Coins</p>
        </Panel>
        <Panel title="Expiring Soon (30 days)">
          <div className="mb-3 text-3xl font-bold text-emerald-600">{expiring?.total_amount_remaining ?? 0} coins</div>
          {expiring?.grants?.length ? (
            <div className="space-y-2 text-sm">
              {expiring.grants.map((g: any) => (
                <div key={g.coin_grant_id} className="flex justify-between rounded-md bg-slate-50 px-3 py-2">
                  <span>Expires {g.expiry_date ?? "No expiry"}</span>
                  <span className="font-medium">{g.amount_remaining}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No coins expiring soon.</p>
          )}
        </Panel>

        <Panel title="Recent Transactions">
          {txs?.length ? (
            <div className="space-y-2 text-sm">
              {txs.map((t: any) => (
                <div key={t.transaction_id} className="flex justify-between rounded-md bg-slate-50 px-3 py-2">
                  <span className="capitalize">{t.direction}</span>
                  <span className="font-medium">{t.amount}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No transactions yet.</p>
          )}
        </Panel>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel title="Recent Rewards">
          {rewards?.length ? (
            <div className="space-y-2 text-sm">
              {rewards.map((r: any, idx: number) => (
                <div key={`${r.redeemed_at}-${idx}`} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <div className="font-medium">{r.reward_title ?? "Reward"}</div>
                  <div className="text-slate-500">Redeemed: {r.redeemed_at}</div>
                  {r.voucher_code ? <div className="mt-2 font-mono text-emerald-600">Voucher: {r.voucher_code}</div> : null}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No rewards redeemed yet.</p>
          )}
        </Panel>

        <div className="lg:col-span-2">
          <Panel title="Travel Campaigns and Missions">
            <div className="mb-6 grid gap-3 sm:grid-cols-2">
              {campaigns?.length ? (
                campaigns.slice(0, 4).map((c: any) => (
                  <div key={c.campaign_id} className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-3 text-sm">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-slate-500">Eligibility: {c.eligibility_type}</div>
                    {c.participation_status ? <div className="mt-2 font-medium text-emerald-700">Status: {c.participation_status}</div> : null}
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No active campaigns right now.</p>
              )}
            </div>

            <p className="mb-3 text-sm text-slate-600">
              {completedCount} completed / {inProgressCount} in progress or available
            </p>
            <div className="space-y-2">
              {missionProgress?.slice(0, 3).map((m: any) => (
                <div key={m.mission_code} className="flex justify-between rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
                  <span>{m.mission_code}</span>
                  <span className="font-medium capitalize">{String(m.status).replace(/_/g, " ")}</span>
                </div>
              )) ?? null}
            </div>
          </Panel>
        </div>
      </section>
    </div>
  );
}

function Card({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <div className="metric-card">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-bold text-emerald-600">{value}</p>
      {subtitle ? <p className="mt-1 text-xs text-slate-400">{subtitle}</p> : null}
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-24 rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3">
      <p className="text-xl font-bold text-slate-950">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="h-full rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-3 font-semibold text-slate-950">{title}</h3>
      {children}
    </div>
  );
}
