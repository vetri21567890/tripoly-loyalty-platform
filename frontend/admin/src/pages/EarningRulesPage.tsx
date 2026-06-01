import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

const UGC_TYPES = ["photo", "review_screenshot", "testimonial", "video", "reel"];

export default function EarningRulesPage() {
  const [ugcType, setUgcType] = useState("photo");
  const [coins, setCoins] = useState(50);
  const [dailyLimit, setDailyLimit] = useState(5);
  const [monthlyLimit, setMonthlyLimit] = useState(20);
  const queryClient = useQueryClient();
  const { data = [] } = useQuery({
    queryKey: ["admin-ugc-rules"],
    queryFn: () => api.get("/admin/earning-rules/ugc").then((r) => r.data.data),
  });

  const saveUgcRule = async () => {
    await api.post("/admin/earning-rules/ugc", { ugc_type: ugcType, coins_awarded: coins });
    alert("UGC rule saved");
    await queryClient.invalidateQueries({ queryKey: ["admin-ugc-rules"] });
  };

  const saveLimits = async () => {
    await api.post("/admin/earning-rules/ugc-limits", {
      ugc_type: ugcType,
      daily_limit: dailyLimit,
      monthly_limit: monthlyLimit,
    });
    alert("Limits saved");
    await queryClient.invalidateQueries({ queryKey: ["admin-ugc-rules"] });
  };

  return (
    <div className="max-w-lg space-y-8">
      <h2 className="text-2xl font-bold">Earning Rules (no deploy required)</h2>
      <div className="bg-white rounded-xl p-6 shadow space-y-4">
        <h3 className="font-semibold">UGC Coin Values</h3>
        <select value={ugcType} onChange={(e) => setUgcType(e.target.value)} className="w-full border rounded px-4 py-2">
          {UGC_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <input type="number" value={coins} onChange={(e) => setCoins(Number(e.target.value))} className="w-full border rounded px-4 py-2" />
        <button onClick={saveUgcRule} className="w-full bg-admin-primary text-white py-2 rounded">
          Save UGC Rule
        </button>
      </div>
      <div className="bg-white rounded-xl p-6 shadow space-y-4">
        <h3 className="font-semibold">Submission Limits</h3>
        <input type="number" value={dailyLimit} onChange={(e) => setDailyLimit(Number(e.target.value))} aria-label="Daily limit" className="w-full border rounded px-4 py-2" />
        <input type="number" value={monthlyLimit} onChange={(e) => setMonthlyLimit(Number(e.target.value))} aria-label="Monthly limit" className="w-full border rounded px-4 py-2" />
        <button onClick={saveLimits} className="w-full bg-slate-700 text-white py-2 rounded">
          Save Limits
        </button>
      </div>
      <div className="overflow-hidden rounded-lg bg-white shadow">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="p-3 text-left">UGC Type</th>
              <th className="p-3 text-left">Coins</th>
              <th className="p-3 text-left">Daily Limit</th>
              <th className="p-3 text-left">Monthly Limit</th>
              <th className="p-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item: { ugc_type: string; coins_awarded: number; daily_limit: number | null; monthly_limit: number | null; status: string }) => (
              <tr key={item.ugc_type} className="border-t">
                <td className="p-3">{item.ugc_type}</td>
                <td className="p-3">{item.coins_awarded}</td>
                <td className="p-3">{item.daily_limit ?? "-"}</td>
                <td className="p-3">{item.monthly_limit ?? "-"}</td>
                <td className="p-3">{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
