import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export default function AuditLogsPage() {
  const { data } = useQuery({
    queryKey: ["audit"],
    queryFn: () => api.get("/admin/audit-logs").then((r) => r.data.data),
  });

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Audit Logs</h2>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Entity</th>
              <th className="text-left p-3">Time</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((a: { id: string; action_type: string; entity_type: string; created_at: string }) => (
              <tr key={a.id} className="border-t">
                <td className="p-3">{a.action_type}</td>
                <td className="p-3">{a.entity_type}</td>
                <td className="p-3">{new Date(a.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
