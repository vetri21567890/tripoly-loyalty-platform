import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

type WalletRules = {
  coins_per_rupee: number;
  coin_expiry_months: number;
  minimum_redemption_coins: number;
  partial_redemption_allowed: boolean;
  max_redemption_per_booking: number | null;
  conversion_rule: string;
};

const defaults: WalletRules = {
  coins_per_rupee: 10,
  coin_expiry_months: 24,
  minimum_redemption_coins: 500,
  partial_redemption_allowed: true,
  max_redemption_per_booking: null,
  conversion_rule: "10 Travel Coins = ₹1",
};

export default function WalletRulesPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<WalletRules>(defaults);
  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-wallet-rules"],
    queryFn: () => api.get("/admin/program-settings").then((r) => r.data.data as WalletRules),
  });

  useEffect(() => {
    if (data) setForm({ ...defaults, ...data });
  }, [data]);

  const save = useMutation({
    mutationFn: () => api.put("/admin/program-settings/wallet-rules", form).then((r) => r.data.data as WalletRules),
    onSuccess: (saved) => {
      setForm({ ...defaults, ...saved });
      qc.invalidateQueries({ queryKey: ["admin-wallet-rules"] });
      qc.invalidateQueries({ queryKey: ["/admin/program-settings"] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Loyalty Program</p>
        <h2 className="mt-1 text-2xl font-bold text-slate-950">Wallet Rules</h2>
        <p className="mt-2 text-sm text-slate-600">Manage system-wide Travel Coins conversion, expiry, and redemption guardrails.</p>
      </div>

      {isLoading ? <State text="Loading wallet rules..." /> : null}
      {isError ? <State text="Could not load wallet rules." tone="error" /> : null}

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
          <div className="grid gap-4 md:grid-cols-2">
            <NumberField label="Coins per rupee" value={form.coins_per_rupee} onChange={(value) => setForm({ ...form, coins_per_rupee: value, conversion_rule: `${value} Travel Coins = ₹1` })} />
            <NumberField label="Coin expiry months" value={form.coin_expiry_months} onChange={(value) => setForm({ ...form, coin_expiry_months: value })} />
            <NumberField label="Minimum redemption coins" value={form.minimum_redemption_coins} onChange={(value) => setForm({ ...form, minimum_redemption_coins: value })} />
            <NumberField label="Max redemption per booking" value={form.max_redemption_per_booking ?? 0} onChange={(value) => setForm({ ...form, max_redemption_per_booking: value || null })} />
            <label className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-3 text-sm">
              <input type="checkbox" checked={form.partial_redemption_allowed} onChange={(e) => setForm({ ...form, partial_redemption_allowed: e.target.checked })} />
              Partial redemption allowed
            </label>
          </div>
          <button onClick={() => save.mutate()} disabled={save.isPending} className="mt-6 rounded-lg bg-admin-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
            Save Wallet Rules
          </button>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Conversion Rule</p>
          <p className="mt-2 text-2xl font-bold text-slate-950">{form.conversion_rule}</p>
          <div className="mt-5 space-y-2 text-sm text-slate-600">
            <p>2,500 Travel Coins = ₹{Math.floor(2500 / form.coins_per_rupee)}</p>
            <p>5,000 Travel Coins = ₹{Math.floor(5000 / form.coins_per_rupee)}</p>
            <p>10,000 Travel Coins = ₹{Math.floor(10000 / form.coins_per_rupee)}</p>
          </div>
        </div>
      </section>
    </div>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      <input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} className="h-10 w-full rounded-lg border border-slate-300 px-3" />
    </label>
  );
}

function State({ text, tone = "default" }: { text: string; tone?: "default" | "error" }) {
  return <div className={`rounded-lg border p-5 text-sm ${tone === "error" ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-500"}`}>{text}</div>;
}
