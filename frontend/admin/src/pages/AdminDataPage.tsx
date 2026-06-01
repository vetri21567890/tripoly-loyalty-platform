import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "../api/client";

type Column = {
  key: string;
  label: string;
};

type AdminDataPageProps = {
  title: string;
  endpoint: string;
  columns: Column[];
  emptyText?: string;
  description?: string;
  actionLabel?: string;
};

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

export default function AdminDataPage({ title, endpoint, columns, emptyText = "No records found." }: AdminDataPageProps) {
  const [search, setSearch] = useState("");
  const { data = [], isLoading, isError } = useQuery({
    queryKey: [endpoint],
    queryFn: () => api.get(endpoint).then((r) => r.data.data as Record<string, unknown>[]),
  });
  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return data;
    return data.filter((row) => columns.some((column) => formatValue(row[column.key]).toLowerCase().includes(term)));
  }, [columns, data, search]);

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Admin Module</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">{title}</h2>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search records"
            className="h-10 rounded-lg border border-slate-300 px-3 text-sm outline-none focus:border-admin-accent"
          />
        </div>
      </div>
      <div className="mb-3 flex items-center justify-between text-sm text-slate-500">
        <span>{filtered.length} records</span>
        <span>Connected to {endpoint}</span>
      </div>
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead className="bg-slate-50">
              <tr>
                {columns.map((column) => (
                  <th key={column.key} className="whitespace-nowrap p-3 text-left font-semibold text-slate-600">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={columns.length} className="p-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={columns.length} className="p-6 text-center text-red-600">
                    Could not load data.
                  </td>
                </tr>
              )}
              {!isLoading && !isError && filtered.length === 0 && (
                <tr>
                  <td colSpan={columns.length} className="p-6 text-center text-slate-500">
                    {emptyText}
                  </td>
                </tr>
              )}
              {filtered.map((row, index) => (
                <tr key={String(row.id ?? row.customer_id ?? row.campaign_id ?? row.transaction_id ?? index)} className="border-t">
                  {columns.map((column) => (
                    <td key={column.key} className="max-w-[260px] truncate p-3 text-slate-700">
                      {isStatusColumn(column.key) ? <StatusBadge value={formatValue(row[column.key])} /> : formatValue(row[column.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function isStatusColumn(key: string) {
  return ["status", "decision", "direction", "type"].includes(key);
}

function StatusBadge({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const color =
    normalized.includes("active") || normalized.includes("completed") || normalized.includes("approved")
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : normalized.includes("pending") || normalized.includes("invited")
        ? "bg-amber-50 text-amber-700 ring-amber-200"
        : normalized.includes("reject") || normalized.includes("expired")
          ? "bg-red-50 text-red-700 ring-red-200"
          : "bg-slate-50 text-slate-700 ring-slate-200";
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${color}`}>{value}</span>;
}
