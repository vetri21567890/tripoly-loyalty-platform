import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { api } from "../api/client";

export default function DashboardPage() {
  const { data } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => api.get("/analytics/summary").then((r) => r.data.data),
  });
  const { data: customers = [] } = useQuery({
    queryKey: ["admin-customers-overview"],
    queryFn: () => api.get("/admin/customers").then((r) => r.data.data),
  });
  const { data: campaigns = [] } = useQuery({
    queryKey: ["admin-campaigns-overview"],
    queryFn: () => api.get("/admin/campaigns").then((r) => r.data.data),
  });
  const { data: ugc = [] } = useQuery({
    queryKey: ["admin-ugc-overview"],
    queryFn: () => api.get("/admin/ugc/attempts").then((r) => r.data.data),
  });

  const pendingUgc = ugc.filter((item: any) => item.status === "PENDING").length;
  const activeCampaigns = campaigns.filter((item: any) => item.status === "active").length;

  return (
    <div className="space-y-8">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium text-admin-accent">Travel loyalty operations</p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">Analytics Dashboard</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Monitor member engagement, coin liability, referrals, campaigns, and UGC moderation across Tripoly's independent loyalty platform.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <MiniMetric label="Customers" value={customers.length} />
            <MiniMetric label="Campaign Mgmt" value={activeCampaigns} />
            <MiniMetric label="Pending UGC" value={pendingUgc} />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <Metric title="Active Users" value={data?.active_users ?? 0} />
        <Metric title="Lifetime Coins Issued" value={data?.lifetime_coins_issued ?? 0} />
        <Metric title="Coins Redeemed" value={data?.coins_redeemed ?? 0} />
        <Metric title="Referrals Qualified" value={data?.referrals_qualified ?? 0} />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel title="Operations Queue">
          <QueueRow label="UGC awaiting review" value={pendingUgc} />
          <QueueRow label="Campaigns live" value={activeCampaigns} />
          <QueueRow label="Customers visible to admin" value={customers.length} />
        </Panel>
        <Panel title="Retention Levers">
          <div className="space-y-3 text-sm text-slate-600">
            <p>Campaigns, missions, earning rules, and rewards are managed as travel-retention tools, not store catalog flows.</p>
            <p>External booking, CRM, WhatsApp, and travel operations systems should connect through APIs and webhooks.</p>
          </div>
        </Panel>
        <Panel title="Access Model">
          <div className="space-y-3 text-sm text-slate-600">
            <p>Admin APIs require an active admin role assignment.</p>
            <p>Customer APIs remain scoped to the authenticated customer and do not depend on frontend-only guards.</p>
          </div>
        </Panel>
      </section>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-24 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xl font-bold text-slate-950">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="h-full rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-3 font-semibold text-slate-950">{title}</h3>
      {children}
    </div>
  );
}

function QueueRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between border-t border-slate-100 py-3 text-sm first:border-t-0 first:pt-0">
      <span className="text-slate-600">{label}</span>
      <span className="font-semibold text-slate-950">{value}</span>
    </div>
  );
}
