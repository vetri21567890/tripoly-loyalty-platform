import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export default function UgcModerationPage() {
  const [attemptId, setAttemptId] = useState("");
  const [reason, setReason] = useState("");
  const queryClient = useQueryClient();
  const { data = [] } = useQuery({
    queryKey: ["admin-ugc-attempts"],
    queryFn: () => api.get("/admin/ugc/attempts").then((r) => r.data.data),
  });

  const moderate = async (decision: "approve" | "reject") => {
    await api.post(`/admin/ugc/${attemptId}/moderate`, {
      decision,
      rejection_reason: decision === "reject" ? reason : null,
    });
    alert(`UGC ${decision}d`);
    setAttemptId("");
    await queryClient.invalidateQueries({ queryKey: ["admin-ugc-attempts"] });
  };

  return (
    <div className="max-w-lg">
      <h2 className="text-2xl font-bold mb-6">UGC Moderation</h2>
      <div className="bg-white rounded-xl p-6 shadow space-y-4">
        <input
          aria-label="UGC attempt ID"
          value={attemptId}
          onChange={(e) => setAttemptId(e.target.value)}
          className="w-full border rounded px-4 py-2"
        />
        <input
          aria-label="Rejection reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full border rounded px-4 py-2"
        />
        <div className="flex gap-2">
          <button onClick={() => moderate("approve")} className="flex-1 bg-green-600 text-white py-2 rounded">
            Approve
          </button>
          <button onClick={() => moderate("reject")} className="flex-1 bg-red-600 text-white py-2 rounded">
            Reject
          </button>
        </div>
      </div>
      <div className="mt-8 overflow-hidden rounded-lg bg-white shadow">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="p-3 text-left">Attempt ID</th>
              <th className="p-3 text-left">Type</th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3 text-left">Customer</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item: { ugc_attempt_id: string; ugc_type: string; status: string; customer_id: string }) => (
              <tr key={item.ugc_attempt_id} className="border-t">
                <td className="max-w-[220px] truncate p-3">{item.ugc_attempt_id}</td>
                <td className="p-3">{item.ugc_type}</td>
                <td className="p-3">{item.status}</td>
                <td className="max-w-[220px] truncate p-3">{item.customer_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
