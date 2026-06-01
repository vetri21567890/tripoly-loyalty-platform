import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

type Tier = {
  tier_id: string;
  code: string;
  name: string;
  min_lifetime_coins: number;
  max_lifetime_coins: number | null;
  benefits: Record<string, unknown>;
  status: string;
  sort_order: number;
};

const tierCodes = ["EXPLORER", "VOYAGER", "ELITE_TRAVELLER", "GLOBAL_NOMAD"];

export default function TierManagementPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<Tier | null>(null);
  const { data: tiers = [], isLoading, isError } = useQuery({
    queryKey: ["admin-tiers"],
    queryFn: () => api.get("/admin/tiers").then((r) => r.data.data as Tier[]),
  });

  const save = useMutation({
    mutationFn: (tier: Tier) =>
      api.put(`/admin/tiers/${tier.tier_id}`, {
        code: tier.code,
        name: tier.name,
        min_lifetime_coins: Number(tier.min_lifetime_coins),
        max_lifetime_coins: tier.max_lifetime_coins === null || tier.max_lifetime_coins === undefined ? null : Number(tier.max_lifetime_coins),
        benefits: tier.benefits || {},
        status: tier.status,
        sort_order: Number(tier.sort_order),
      }),
    onSuccess: () => {
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["admin-tiers"] });
    },
  });

  const toggle = (tier: Tier) => save.mutate({ ...tier, status: tier.status === "active" ? "inactive" : "active" });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Loyalty Program</p>
        <h2 className="mt-1 text-2xl font-bold text-slate-950">Tiers / VIP</h2>
        <p className="mt-2 text-sm text-slate-600">Tiers are based on lifetime coins earned. Redeeming coins does not reduce a customer's tier.</p>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full min-w-[900px] text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="p-3 text-left">Order</th>
              <th className="p-3 text-left">Code</th>
              <th className="p-3 text-left">Tier</th>
              <th className="p-3 text-left">Min Lifetime Coins</th>
              <th className="p-3 text-left">Max Lifetime Coins</th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? <RowMessage colSpan={7} text="Loading tiers..." /> : null}
            {isError ? <RowMessage colSpan={7} text="Could not load tiers." tone="error" /> : null}
            {!isLoading && !isError && !tiers.length ? <RowMessage colSpan={7} text="No tiers configured." /> : null}
            {tiers.map((tier) => (
              <tr key={tier.tier_id} className="border-t">
                <td className="p-3">{tier.sort_order}</td>
                <td className="p-3 font-mono text-xs">{tier.code}</td>
                <td className="p-3 font-medium">{tier.name}</td>
                <td className="p-3">{tier.min_lifetime_coins}</td>
                <td className="p-3">{tier.max_lifetime_coins ?? "No max"}</td>
                <td className="p-3">
                  <span className={`rounded-full px-2 py-1 text-xs font-medium ${tier.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                    {tier.status}
                  </span>
                </td>
                <td className="space-x-2 p-3">
                  <button onClick={() => setEditing(tier)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium">
                    Edit
                  </button>
                  <button onClick={() => toggle(tier)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium">
                    {tier.status === "active" ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing ? <TierEditor tier={editing} onChange={setEditing} onClose={() => setEditing(null)} onSave={() => save.mutate(editing)} saving={save.isPending} /> : null}
    </div>
  );
}

function TierEditor({ tier, onChange, onClose, onSave, saving }: { tier: Tier; onChange: (tier: Tier) => void; onClose: () => void; onSave: () => void; saving: boolean }) {
  const [benefitsText, setBenefitsText] = useState(JSON.stringify(tier.benefits || {}, null, 2));
  useEffect(() => setBenefitsText(JSON.stringify(tier.benefits || {}, null, 2)), [tier.tier_id]);

  const updateBenefits = (value: string) => {
    setBenefitsText(value);
    try {
      onChange({ ...tier, benefits: JSON.parse(value || "{}") });
    } catch {
      // Keep editing text until valid JSON is entered.
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-950">Edit Tier</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Field label="Tier code">
            <select value={tier.code} onChange={(e) => onChange({ ...tier, code: e.target.value })} className="h-10 w-full rounded-lg border border-slate-300 px-3">
              {tierCodes.map((code) => (
                <option key={code} value={code}>{code}</option>
              ))}
            </select>
          </Field>
          <Field label="Tier name">
            <input value={tier.name} onChange={(e) => onChange({ ...tier, name: e.target.value })} className="h-10 w-full rounded-lg border border-slate-300 px-3" />
          </Field>
          <Field label="Min lifetime coins">
            <input type="number" value={tier.min_lifetime_coins} onChange={(e) => onChange({ ...tier, min_lifetime_coins: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-slate-300 px-3" />
          </Field>
          <Field label="Max lifetime coins">
            <input type="number" value={tier.max_lifetime_coins ?? ""} onChange={(e) => onChange({ ...tier, max_lifetime_coins: e.target.value ? Number(e.target.value) : null })} className="h-10 w-full rounded-lg border border-slate-300 px-3" />
          </Field>
          <Field label="Display order">
            <input type="number" value={tier.sort_order} onChange={(e) => onChange({ ...tier, sort_order: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-slate-300 px-3" />
          </Field>
          <Field label="Status">
            <select value={tier.status} onChange={(e) => onChange({ ...tier, status: e.target.value })} className="h-10 w-full rounded-lg border border-slate-300 px-3">
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </select>
          </Field>
        </div>
        <Field label="Tier benefits JSON">
          <textarea value={benefitsText} onChange={(e) => updateBenefits(e.target.value)} rows={5} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
        </Field>
        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancel</button>
          <button onClick={onSave} disabled={saving} className="rounded-lg bg-admin-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60">Save Changes</button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="text-sm"><span className="mb-1 block font-medium text-slate-700">{label}</span>{children}</label>;
}

function RowMessage({ colSpan, text, tone = "default" }: { colSpan: number; text: string; tone?: "default" | "error" }) {
  return <tr><td colSpan={colSpan} className={`p-6 text-center text-sm ${tone === "error" ? "text-red-600" : "text-slate-500"}`}>{text}</td></tr>;
}
