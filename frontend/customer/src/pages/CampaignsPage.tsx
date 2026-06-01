import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { campaignsApi } from "../api/services";

export default function CampaignsPage() {
  const qc = useQueryClient();
  const { data: campaigns } = useQuery({ queryKey: ["campaigns"], queryFn: () => campaignsApi.list().then((r) => r.data.data) });

  const enroll = useMutation({
    mutationFn: (id: string) => campaignsApi.enroll(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns"] }),
  });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">Travel Campaigns</p>
        <h2 className="page-title">Active Campaigns</h2>
        <p className="page-subtitle">Join eligible travel-loyalty campaigns, complete missions, and earn Travel Coins.</p>
      </section>

      {!campaigns?.length ? (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">No active campaigns are available right now.</div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        {campaigns?.map((c: any) => {
          const eligibility = String(c.eligibility_type);
          const notJoined = c.participation_status == null || c.participation_status === "";
          const tasks = Array.isArray(c.tasks) ? c.tasks : [];
          return (
            <div key={String(c.campaign_id)} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-200 hover:shadow-md">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-slate-950">{String(c.name)}</h3>
                  <p className="mt-1 text-sm text-slate-500 capitalize">{String(c.type).replace(/_/g, " ")}</p>
                </div>
                <span className="status-pill">{Number(c.reward_coins ?? 0).toLocaleString()} coins</span>
              </div>
              {c.description ? <p className="mt-3 text-sm text-slate-600">{String(c.description)}</p> : null}
              <p className="mt-3 text-xs font-medium uppercase tracking-[0.12em] text-slate-400">{eligibility.replace(/_/g, " ")}</p>
              {tasks.length ? (
                <div className="mt-4 space-y-2">
                  {tasks.map((task: string) => (
                    <div key={task} className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-slate-700">{task}</div>
                  ))}
                </div>
              ) : null}
              {eligibility === "ENROLLED_ONLY" && notJoined ? (
                <button onClick={() => enroll.mutate(String(c.campaign_id))} disabled={enroll.isPending} className="primary-button mt-5">
                  Join Campaign
                </button>
              ) : null}
              {eligibility === "ENROLLED_ONLY" && !notJoined ? <p className="mt-5 text-sm font-semibold text-emerald-600">Enrolled</p> : null}
              {eligibility === "INVITE_ONLY" && Boolean(c.invitation_status) && notJoined ? (
                <button onClick={() => enroll.mutate(String(c.campaign_id))} disabled={enroll.isPending} className="primary-button mt-5">
                  Accept Invitation
                </button>
              ) : null}
              {eligibility === "INVITE_ONLY" && !notJoined ? <p className="mt-5 text-sm font-semibold text-emerald-600">Joined</p> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
