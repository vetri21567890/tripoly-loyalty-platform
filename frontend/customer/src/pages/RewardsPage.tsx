import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { rewardsApi, walletApi } from "../api/services";

export default function RewardsPage() {
  const qc = useQueryClient();
  const { data: catalog = [], isLoading } = useQuery({ queryKey: ["catalog"], queryFn: () => rewardsApi.catalog().then((r) => r.data.data) });
  const { data: history = [] } = useQuery({ queryKey: ["reward-history"], queryFn: () => rewardsApi.history(20).then((r) => r.data.data) });
  const { data: wallet } = useQuery({ queryKey: ["wallet"], queryFn: () => walletApi.balance().then((r) => r.data.data) });

  const redeem = useMutation({
    mutationFn: (rewardId: string) => rewardsApi.redeem(rewardId, `redeem-${rewardId}-${Date.now()}`).then((r) => r.data.data),
    onSuccess: (d) => {
      qc.invalidateQueries({ queryKey: ["wallet"] });
      qc.invalidateQueries({ queryKey: ["catalog"] });
      qc.invalidateQueries({ queryKey: ["reward-history"] });
      alert(d?.voucher_code ? `Reward redeemed. Voucher: ${d.voucher_code}` : "Reward redeemed successfully.");
    },
    onError: (e: { response?: { data?: { message?: string; detail?: { message?: string } } } }) => {
      alert(e.response?.data?.detail?.message || e.response?.data?.message || "Redemption failed");
    },
  });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">Travel Rewards</p>
        <h2 className="page-title">Rewards</h2>
        <p className="page-subtitle">Redeem Tripoly Travel Coins for vouchers, upgrades, lounge passes, experiences, discounts, and merchandise.</p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {isLoading ? <EmptyCard text="Loading rewards..." /> : null}
        {!isLoading && !catalog.length ? <EmptyCard text="No rewards available right now." /> : null}
        {catalog.map((reward) => (
          <div key={reward.reward_catalog_id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-200 hover:shadow-md">
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-semibold text-slate-950">{reward.title}</h3>
              <span className="status-pill">{reward.cost_coins} coins</span>
            </div>
            <p className="mt-3 text-sm text-slate-500">
              {reward.unlimited_inventory ? "Available while active" : `${reward.inventory_remaining ?? 0} remaining`}
            </p>
            <p className="mt-2 text-sm text-slate-600">Approx value: ₹{reward.approx_value_inr ?? Math.floor(reward.cost_coins / (wallet?.coins_per_rupee ?? 10))}</p>
            <p className="mt-1 text-xs text-slate-500">Your balance: {wallet?.available_coins ?? 0} Travel Coins</p>
            <button
              onClick={() => redeem.mutate(reward.reward_catalog_id)}
              disabled={redeem.isPending || (wallet?.available_coins ?? 0) < reward.cost_coins}
              className="mt-5 w-full rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
            >
              {(wallet?.available_coins ?? 0) < reward.cost_coins ? "Insufficient Coins" : "Redeem Reward"}
            </button>
          </div>
        ))}
      </section>

      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <h3 className="font-semibold text-slate-950">Redemption History</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {history.length ? (
            history.map((item: any, index) => (
              <div key={`${item.redeemed_at}-${index}`} className="grid gap-2 p-4 text-sm md:grid-cols-4">
                <span className="font-medium text-slate-950">{item.reward_title ?? "Reward"}</span>
                <span>{item.coins_spent} coins</span>
                <span className="capitalize">{String(item.status).replace(/_/g, " ")}</span>
                <span className="font-mono text-emerald-600">{item.voucher_code ?? "-"}</span>
              </div>
            ))
          ) : (
            <p className="p-5 text-sm text-slate-500">No redemptions yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function EmptyCard({ text }: { text: string }) {
  return <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">{text}</div>;
}
