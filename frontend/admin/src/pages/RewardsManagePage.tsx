import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export default function RewardsManagePage() {
  const [title, setTitle] = useState("");
  const [cost, setCost] = useState(100);
  const [unlimited, setUnlimited] = useState(true);
  const queryClient = useQueryClient();
  const { data = [] } = useQuery({
    queryKey: ["admin-reward-catalog"],
    queryFn: () => api.get("/rewards/catalog").then((r) => r.data.data),
  });

  const create = async () => {
    await api.post("/admin/rewards/catalog", {
      title,
      reward_type: "discount_voucher",
      cost_coins: cost,
      unlimited_inventory: unlimited,
      inventory_count: unlimited ? null : 100,
    });
    alert("Reward created");
    setTitle("");
    await queryClient.invalidateQueries({ queryKey: ["admin-reward-catalog"] });
  };

  return (
    <div className="max-w-lg">
      <h2 className="text-2xl font-bold mb-6">Reward Management</h2>
      <div className="bg-white rounded-xl p-6 shadow space-y-4">
        <input aria-label="Reward title" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full border rounded px-4 py-2" />
        <input type="number" value={cost} onChange={(e) => setCost(Number(e.target.value))} className="w-full border rounded px-4 py-2" />
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={unlimited} onChange={(e) => setUnlimited(e.target.checked)} />
          Unlimited inventory
        </label>
        <button onClick={create} className="w-full bg-admin-primary text-white py-2 rounded">
          Create Reward
        </button>
      </div>
      <div className="mt-8 overflow-hidden rounded-lg bg-white shadow">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="p-3 text-left">Reward</th>
              <th className="p-3 text-left">Type</th>
              <th className="p-3 text-left">Cost</th>
              <th className="p-3 text-left">Inventory</th>
              <th className="p-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item: { reward_catalog_id: string; title: string; reward_type: string; cost_coins: number; inventory_remaining: number | null; status: string }) => (
              <tr key={item.reward_catalog_id} className="border-t">
                <td className="p-3">{item.title}</td>
                <td className="p-3">{item.reward_type}</td>
                <td className="p-3">{item.cost_coins}</td>
                <td className="p-3">{item.inventory_remaining ?? "Unlimited"}</td>
                <td className="p-3">{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
