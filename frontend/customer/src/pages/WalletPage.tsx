import { useQuery } from "@tanstack/react-query";
import { walletApi } from "../api/services";

export default function WalletPage() {
  const { data: balance, isLoading } = useQuery({ queryKey: ["wallet"], queryFn: () => walletApi.balance().then((r) => r.data.data) });
  const { data: txs = [] } = useQuery({ queryKey: ["transactions"], queryFn: () => walletApi.transactions().then((r) => r.data.data) });
  const { data: expiring } = useQuery({ queryKey: ["wallet-expiring"], queryFn: () => walletApi.expiringSoon(30, 20).then((r) => r.data.data) });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">Travel Wallet</p>
        <h2 className="page-title">Wallet</h2>
        <p className="page-subtitle">Track available, lifetime, redeemed, expired, and expiring Tripoly Travel Coins.</p>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Available Coins" value={balance?.available_coins ?? 0} loading={isLoading} />
        <Metric label="Approx Redemption Value" value={balance?.approx_redemption_value_inr ?? 0} loading={isLoading} prefix="₹" />
        <Metric label="Lifetime Coins" value={balance?.lifetime_coins_earned ?? 0} loading={isLoading} />
        <Metric label="Redeemed Coins" value={balance?.redeemed_coins_to_date ?? 0} loading={isLoading} />
        <Metric label="Expired Coins" value={balance?.expired_coins ?? 0} loading={isLoading} />
      </div>

      <div className="panel-card">
        <p className="text-sm text-slate-500">Conversion Rule</p>
        <p className="mt-2 text-2xl font-bold text-emerald-600">{balance?.conversion_rule ?? "10 Travel Coins = ₹1"}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="panel-card">
          <h3 className="font-semibold text-slate-950">Expiring Soon</h3>
          <p className="mt-2 text-3xl font-bold text-emerald-600">{expiring?.total_amount_remaining ?? 0}</p>
          <p className="text-sm text-slate-500">coins in the next {expiring?.days ?? 30} days</p>
          <div className="mt-4 space-y-2">
            {expiring?.grants?.length ? (
              expiring.grants.map((grant) => (
                <div key={grant.coin_grant_id} className="flex justify-between rounded-md bg-emerald-50 px-3 py-2 text-sm">
                  <span>{grant.expiry_date ?? "No expiry"}</span>
                  <span className="font-medium">{grant.amount_remaining}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">No coins expiring soon.</p>
            )}
          </div>
        </section>

        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm lg:col-span-2">
          <div className="border-b border-slate-100 px-5 py-4">
            <h3 className="font-semibold text-slate-950">Transaction History</h3>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="p-3 text-left">Type</th>
                <th className="p-3 text-left">Amount</th>
                <th className="p-3 text-left">Reason</th>
                <th className="p-3 text-left">Date</th>
              </tr>
            </thead>
            <tbody>
              {txs.length ? (
                txs.map((t) => (
                  <tr key={t.transaction_id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-3 capitalize">{t.direction}</td>
                    <td className="p-3 font-medium">{t.amount}</td>
                    <td className="p-3">{t.reason_code}</td>
                    <td className="p-3">{new Date(t.created_at).toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="p-6 text-center text-slate-500" colSpan={4}>
                    No wallet activity yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}

function Metric({ label, value, loading, prefix = "" }: { label: string; value: number; loading: boolean; prefix?: string }) {
  return (
    <div className="metric-card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-emerald-600">{loading ? "-" : `${prefix}${value}`}</p>
    </div>
  );
}
