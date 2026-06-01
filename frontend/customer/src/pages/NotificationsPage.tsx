import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notificationsApi } from "../api/services";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const { data: inbox } = useQuery({ queryKey: ["inbox"], queryFn: () => notificationsApi.inbox().then((r) => r.data.data) });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbox", "unread"] }),
  });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">Loyalty Inbox</p>
        <h2 className="page-title">Notifications</h2>
        <p className="page-subtitle">Reward, campaign, referral, UGC, and tier updates from Tripoly.</p>
      </section>
      <ul className="space-y-2">
        {inbox?.map((n) => (
          <li
            key={n.id}
            className={`rounded-lg bg-white p-4 shadow-sm border ${!n.read_at ? "border-emerald-300" : "border-slate-200"}`}
          >
            <div className="flex justify-between">
              <div>
                <p className="font-medium">{n.title}</p>
                <p className="text-sm text-slate-500">{n.body}</p>
              </div>
              {!n.read_at && (
                <button onClick={() => markRead.mutate(n.id)} className="text-xs font-semibold text-emerald-600">
                  Mark read
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
