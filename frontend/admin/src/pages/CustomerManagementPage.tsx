import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

type Customer = {
  customer_id: string;
  email: string | null;
  phone: string | null;
  first_name: string | null;
  last_name: string | null;
  status: string;
  available_coins: number;
  lifetime_coins_earned: number;
  created_at: string;
};

type CustomerForm = {
  email: string;
  phone: string;
  password: string;
  first_name: string;
  last_name: string;
  status: "active" | "inactive" | "blocked";
};

const emptyForm: CustomerForm = {
  email: "",
  phone: "",
  password: "",
  first_name: "",
  last_name: "",
  status: "active",
};

export default function CustomerManagementPage() {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<CustomerForm>(emptyForm);

  const { data = [], isLoading, isError } = useQuery({
    queryKey: ["admin-customers"],
    queryFn: () => api.get("/admin/customers").then((r) => r.data.data as Customer[]),
  });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return data;
    return data.filter((item) =>
      [item.email, item.phone, item.first_name, item.last_name, item.status].some((value) => String(value ?? "").toLowerCase().includes(q)),
    );
  }, [data, query]);

  const create = useMutation({
    mutationFn: () =>
      api.post("/admin/customers", {
        email: form.email || null,
        phone: form.phone || null,
        password: form.password || null,
        first_name: form.first_name || null,
        last_name: form.last_name || null,
        status: form.status,
      }),
    onSuccess: () => {
      setModalOpen(false);
      setForm(emptyForm);
      qc.invalidateQueries({ queryKey: ["admin-customers"] });
      qc.invalidateQueries({ queryKey: ["admin-customers-overview"] });
    },
  });

  const exportCsv = () => {
    const rows = filtered.map((item) => ({
      customer_id: item.customer_id,
      first_name: item.first_name ?? "",
      last_name: item.last_name ?? "",
      email: item.email ?? "",
      phone: item.phone ?? "",
      status: item.status,
      available_coins: item.available_coins,
      lifetime_coins_earned: item.lifetime_coins_earned,
      created_at: item.created_at,
    }));
    downloadCsv("tripoly-customers.csv", rows);
  };

  const activeCount = data.filter((item) => item.status === "active").length;
  const totalCoins = data.reduce((sum, item) => sum + Number(item.available_coins || 0), 0);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Core</p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">Customer Management</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">Add customers, review wallet balances, and export customer records for travel-loyalty operations.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button onClick={exportCsv} disabled={!filtered.length} className="h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:border-emerald-500 hover:text-emerald-700 disabled:opacity-50">
              Export CSV
            </button>
            <button onClick={() => setModalOpen(true)} className="h-10 rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700">
              Add Customer
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Metric label="Total Customers" value={data.length} />
        <Metric label="Active Customers" value={activeCount} accent />
        <Metric label="Available Coins" value={totalCoins.toLocaleString()} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-200 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="font-semibold text-slate-950">Customers</h3>
            <p className="text-sm text-slate-500">Customer account and wallet visibility for admins.</p>
          </div>
          <input
            aria-label="Search customers"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-10 w-full rounded-lg border border-slate-300 px-3 text-sm outline-none focus:border-emerald-500 md:w-72"
          />
        </div>

        {isLoading ? <State text="Loading customers..." /> : null}
        {isError ? <State text="Could not load customers." tone="error" /> : null}
        {!isLoading && !isError && filtered.length === 0 ? <EmptyState onCreate={() => setModalOpen(true)} /> : null}

        {filtered.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.12em] text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Customer</th>
                  <th className="px-4 py-3 font-semibold">Contact</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Wallet</th>
                  <th className="px-4 py-3 font-semibold">Joined</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((customer) => (
                  <tr key={customer.customer_id} className="border-t border-slate-100 hover:bg-slate-50/70">
                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-950">{displayName(customer)}</div>
                      <div className="mt-1 font-mono text-xs text-slate-400">{customer.customer_id}</div>
                    </td>
                    <td className="px-4 py-4 text-slate-600">
                      <div>{customer.email || "-"}</div>
                      <div>{customer.phone || "-"}</div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold capitalize ${customer.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                        {customer.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      <div className="font-semibold">{customer.available_coins.toLocaleString()} available</div>
                      <div className="text-xs text-slate-500">{customer.lifetime_coins_earned.toLocaleString()} lifetime</div>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{formatDate(customer.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {modalOpen ? (
        <CustomerModal form={form} setForm={setForm} saving={create.isPending} error={create.isError} onClose={() => setModalOpen(false)} onSave={() => create.mutate()} />
      ) : null}
    </div>
  );
}

function CustomerModal({
  form,
  setForm,
  saving,
  error,
  onClose,
  onSave,
}: {
  form: CustomerForm;
  setForm: (form: CustomerForm) => void;
  saving: boolean;
  error: boolean;
  onClose: () => void;
  onSave: () => void;
}) {
  const canSave = Boolean(form.email.trim() || form.phone.trim());
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
        <div className="border-b border-slate-200 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Customer Setup</p>
          <h3 className="mt-1 text-xl font-bold text-slate-950">Add Customer</h3>
        </div>
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <Field label="First name">
            <input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} className="field" />
          </Field>
          <Field label="Last name">
            <input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} className="field" />
          </Field>
          <Field label="Email">
            <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} className="field" />
          </Field>
          <Field label="Phone">
            <input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} className="field" />
          </Field>
          <Field label="Temporary password">
            <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className="field" />
          </Field>
          <Field label="Status">
            <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as CustomerForm["status"] })} className="field">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="blocked">Blocked</option>
            </select>
          </Field>
        </div>
        {error ? <div className="mx-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">Customer could not be created. Check duplicate email/phone and password length.</div> : null}
        <div className="flex justify-end gap-3 border-t border-slate-200 p-5">
          <button onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
            Cancel
          </button>
          <button onClick={onSave} disabled={saving || !canSave} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
            Add Customer
          </button>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
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
      <h3 className="text-lg font-semibold text-slate-950">No customers found</h3>
      <p className="mt-2 text-sm text-slate-500">Add a customer or adjust your search.</p>
      <button onClick={onCreate} className="mt-5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white">
        Add Customer
      </button>
    </div>
  );
}

function State({ text, tone = "default" }: { text: string; tone?: "default" | "error" }) {
  return <div className={`m-4 rounded-lg border p-5 text-sm ${tone === "error" ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-slate-50 text-slate-500"}`}>{text}</div>;
}

function displayName(customer: Customer) {
  const name = [customer.first_name, customer.last_name].filter(Boolean).join(" ").trim();
  return name || customer.email || customer.phone || "Customer";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

function downloadCsv(filename: string, rows: Array<Record<string, string | number>>) {
  const headers = Object.keys(rows[0] ?? {});
  const csv = [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => csvCell(row[header])).join(",")),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function csvCell(value: string | number) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}
