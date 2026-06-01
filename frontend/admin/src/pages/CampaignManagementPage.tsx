import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

type CampaignStatus = "draft" | "active" | "ended" | "archived";

type Campaign = {
  campaign_id: string;
  name: string;
  description: string | null;
  type: "festival" | "destination_launch" | "insider";
  eligibility_type: "ALL_CUSTOMERS" | "ENROLLED_ONLY" | "INVITE_ONLY";
  reward_coins: number;
  tasks: string[];
  status: CampaignStatus;
  start_at: string | null;
  end_at: string | null;
  participants: number;
};

type CampaignForm = Omit<Campaign, "campaign_id" | "participants">;

const emptyForm: CampaignForm = {
  name: "",
  description: "",
  type: "destination_launch",
  eligibility_type: "ALL_CUSTOMERS",
  reward_coins: 500,
  tasks: ["Join campaign"],
  status: "draft",
  start_at: "",
  end_at: "",
};

const statusTone: Record<CampaignStatus, string> = {
  draft: "bg-slate-100 text-slate-700",
  active: "bg-emerald-100 text-emerald-700",
  ended: "bg-amber-100 text-amber-800",
  archived: "bg-zinc-100 text-zinc-600",
};

export default function CampaignManagementPage() {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Campaign | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<CampaignForm>(emptyForm);

  const { data = [], isLoading, isError } = useQuery({
    queryKey: ["admin-campaigns"],
    queryFn: () => api.get("/admin/campaigns").then((r) => r.data.data as Campaign[]),
  });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return data;
    return data.filter((item) => [item.name, item.description, item.eligibility_type, item.status].some((value) => String(value ?? "").toLowerCase().includes(q)));
  }, [data, query]);

  const save = useMutation({
    mutationFn: () => {
      const payload = serializeForm(form);
      if (editing) return api.put(`/admin/campaigns/${editing.campaign_id}`, payload);
      return api.post("/admin/campaigns", payload);
    },
    onSuccess: () => {
      setModalOpen(false);
      setEditing(null);
      setForm(emptyForm);
      qc.invalidateQueries({ queryKey: ["admin-campaigns"] });
      qc.invalidateQueries({ queryKey: ["admin-campaigns-overview"] });
    },
  });

  const statusUpdate = useMutation({
    mutationFn: ({ campaign, status }: { campaign: Campaign; status: CampaignStatus }) =>
      api.put(`/admin/campaigns/${campaign.campaign_id}`, serializeForm({ ...campaign, status })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-campaigns"] }),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setModalOpen(true);
  };

  const openEdit = (campaign: Campaign) => {
    setEditing(campaign);
    setForm({
      name: campaign.name,
      description: campaign.description ?? "",
      type: campaign.type,
      eligibility_type: campaign.eligibility_type,
      reward_coins: campaign.reward_coins,
      tasks: campaign.tasks ?? [],
      status: campaign.status,
      start_at: toInputDate(campaign.start_at),
      end_at: toInputDate(campaign.end_at),
    });
    setModalOpen(true);
  };

  const activeCount = data.filter((item) => item.status === "active").length;
  const enrolledCount = data.filter((item) => item.eligibility_type === "ENROLLED_ONLY").length;
  const inviteOnlyCount = data.filter((item) => item.eligibility_type === "INVITE_ONLY").length;

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Loyalty Program</p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">Campaign Management</h2>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Manage travel-loyalty campaigns, eligibility, reward coins, and engagement tasks for Tripoly's independent retention platform.
            </p>
          </div>
          <button onClick={openCreate} className="h-10 rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700">
            Create Campaign
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Total Campaigns" value={data.length} />
        <Metric label="Active" value={activeCount} accent />
        <Metric label="Enrollment" value={enrolledCount} />
        <Metric label="Invite Only" value={inviteOnlyCount} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-200 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="font-semibold text-slate-950">Campaign Configuration</h3>
            <p className="text-sm text-slate-500">All admin campaigns, including drafts and archived travel campaigns.</p>
          </div>
          <input
            aria-label="Search campaigns"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-10 w-full rounded-lg border border-slate-300 px-3 text-sm outline-none focus:border-emerald-500 md:w-72"
          />
        </div>

        {isLoading ? <State text="Loading campaigns..." /> : null}
        {isError ? <State text="Could not load campaigns." tone="error" /> : null}
        {!isLoading && !isError && filtered.length === 0 ? <EmptyState onCreate={openCreate} /> : null}

        {filtered.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.12em] text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Campaign</th>
                  <th className="px-4 py-3 font-semibold">Eligibility</th>
                  <th className="px-4 py-3 font-semibold">Reward</th>
                  <th className="px-4 py-3 font-semibold">Window</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((campaign) => (
                  <tr key={campaign.campaign_id} className="border-t border-slate-100 align-top hover:bg-slate-50/70">
                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-950">{campaign.name}</div>
                      <div className="mt-1 max-w-md text-sm text-slate-500">{campaign.description || "No description"}</div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {(campaign.tasks ?? []).slice(0, 3).map((task) => (
                          <span key={task} className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                            {task}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">{labelize(campaign.eligibility_type)}</td>
                    <td className="px-4 py-4 font-semibold text-slate-950">{campaign.reward_coins.toLocaleString()} coins</td>
                    <td className="px-4 py-4 text-slate-600">
                      <div>{formatDate(campaign.start_at) || "No start"}</div>
                      <div>{formatDate(campaign.end_at) || "No end"}</div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold capitalize ${statusTone[campaign.status]}`}>{campaign.status}</span>
                      <div className="mt-2 text-xs text-slate-500">{campaign.participants} enrolled</div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap gap-2">
                        <button onClick={() => openEdit(campaign)} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:border-emerald-500 hover:text-emerald-700">
                          Edit
                        </button>
                        {campaign.status === "active" ? (
                          <button onClick={() => statusUpdate.mutate({ campaign, status: "archived" })} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:border-amber-500 hover:text-amber-700">
                            Deactivate
                          </button>
                        ) : (
                          <button onClick={() => statusUpdate.mutate({ campaign, status: "active" })} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700">
                            Activate
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {modalOpen ? (
        <CampaignModal
          editing={editing}
          form={form}
          setForm={setForm}
          saving={save.isPending}
          error={save.isError}
          onClose={() => setModalOpen(false)}
          onSave={() => save.mutate()}
        />
      ) : null}
    </div>
  );
}

function CampaignModal({
  editing,
  form,
  setForm,
  saving,
  error,
  onClose,
  onSave,
}: {
  editing: Campaign | null;
  form: CampaignForm;
  setForm: (form: CampaignForm) => void;
  saving: boolean;
  error: boolean;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white shadow-xl">
        <div className="border-b border-slate-200 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Campaign Setup</p>
          <h3 className="mt-1 text-xl font-bold text-slate-950">{editing ? "Edit Campaign" : "Create Campaign"}</h3>
        </div>
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <Field label="Campaign name">
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="field" />
          </Field>
          <Field label="Reward coins">
            <input type="number" value={form.reward_coins} onChange={(event) => setForm({ ...form, reward_coins: Number(event.target.value) })} className="field" />
          </Field>
          <Field label="Eligibility type">
            <select value={form.eligibility_type} onChange={(event) => setForm({ ...form, eligibility_type: event.target.value as CampaignForm["eligibility_type"] })} className="field">
              <option value="ALL_CUSTOMERS">All customers</option>
              <option value="ENROLLED_ONLY">Enrolled only</option>
              <option value="INVITE_ONLY">Invite only</option>
            </select>
          </Field>
          <Field label="Campaign status">
            <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as CampaignStatus })} className="field">
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="ended">Ended</option>
              <option value="archived">Archived</option>
            </select>
          </Field>
          <Field label="Campaign type">
            <select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as CampaignForm["type"] })} className="field">
              <option value="destination_launch">Destination launch</option>
              <option value="festival">Seasonal / festival</option>
              <option value="insider">Insider travel</option>
            </select>
          </Field>
          <Field label="Start date">
            <input type="datetime-local" value={form.start_at ?? ""} onChange={(event) => setForm({ ...form, start_at: event.target.value })} className="field" />
          </Field>
          <Field label="End date">
            <input type="datetime-local" value={form.end_at ?? ""} onChange={(event) => setForm({ ...form, end_at: event.target.value })} className="field" />
          </Field>
          <Field label="Campaign tasks / missions">
            <textarea
              value={(form.tasks ?? []).join("\n")}
              onChange={(event) => setForm({ ...form, tasks: event.target.value.split("\n") })}
              className="field min-h-28 py-2"
            />
          </Field>
          <div className="md:col-span-2">
            <Field label="Campaign description">
              <textarea value={form.description ?? ""} onChange={(event) => setForm({ ...form, description: event.target.value })} className="field min-h-24 py-2" />
            </Field>
          </div>
        </div>
        {error ? <div className="mx-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">Campaign could not be saved. Check required fields and try again.</div> : null}
        <div className="flex justify-end gap-3 border-t border-slate-200 p-5">
          <button onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
            Cancel
          </button>
          <button onClick={onSave} disabled={saving || !form.name.trim()} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
            Save Campaign
          </button>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${accent ? "text-emerald-600" : "text-slate-950"}`}>{value}</p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="text-sm">
      <span className="mb-1 block font-semibold text-slate-700">{label}</span>
      {children}
    </label>
  );
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="p-10 text-center">
      <h3 className="text-lg font-semibold text-slate-950">No campaigns yet</h3>
      <p className="mt-2 text-sm text-slate-500">Create a travel-loyalty campaign to manage rewards, eligibility, and engagement tasks.</p>
      <button onClick={onCreate} className="mt-5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white">
        Create Campaign
      </button>
    </div>
  );
}

function State({ text, tone = "default" }: { text: string; tone?: "default" | "error" }) {
  return <div className={`m-4 rounded-lg border p-5 text-sm ${tone === "error" ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-500"}`}>{text}</div>;
}

function serializeForm(form: CampaignForm) {
  return {
    name: form.name,
    description: form.description || null,
    type: form.type,
    eligibility_type: form.eligibility_type,
    reward_coins: Number(form.reward_coins) || 0,
    tasks: (form.tasks ?? []).map((task) => task.trim()).filter(Boolean),
    status: form.status,
    start_at: form.start_at ? new Date(form.start_at).toISOString() : null,
    end_at: form.end_at ? new Date(form.end_at).toISOString() : null,
  };
}

function toInputDate(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16);
}

function formatDate(value: string | null) {
  if (!value) return null;
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

function labelize(value: string) {
  return value.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}
