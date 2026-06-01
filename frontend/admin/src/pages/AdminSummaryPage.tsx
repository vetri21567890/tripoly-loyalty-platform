import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

type AdminSummaryPageProps = {
  title: string;
  endpoint: string;
  description: string;
};

function titleize(value: string) {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function flattenMetrics(value: unknown): Array<[string, string | number]> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value as Record<string, unknown>)
    .filter(([, item]) => typeof item === "number" || typeof item === "string")
    .map(([key, item]) => [titleize(key), item as string | number]);
}

export default function AdminSummaryPage({ title, endpoint, description }: AdminSummaryPageProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: [endpoint],
    queryFn: () => api.get(endpoint).then((r) => r.data.data),
  });

  const metrics = flattenMetrics(data?.metrics ?? data);
  const sections = data && typeof data === "object" && !Array.isArray(data) ? Object.entries(data as Record<string, unknown>).filter(([, value]) => Array.isArray(value)) : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Loyalty Configuration</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">{description}</p>
        </div>
      </div>

      {isLoading ? <StateCard text="Loading module data..." /> : null}
      {isError ? <StateCard text="Could not load this module." tone="error" /> : null}

      {metrics.length ? (
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
          {metrics.map(([label, value]) => (
            <div key={label} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
            </div>
          ))}
        </div>
      ) : null}

      {sections.map(([section, rows]) => (
        <div key={section} className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h3 className="font-semibold text-slate-950">{titleize(section)}</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {(rows as Record<string, unknown>[]).length ? (
              (rows as Record<string, unknown>[]).map((row, index) => (
                <div key={String(row.id ?? row.mission_code ?? index)} className="grid gap-3 p-4 text-sm md:grid-cols-4">
                  {Object.entries(row)
                    .slice(0, 8)
                    .map(([key, value]) => (
                      <div key={key}>
                        <p className="text-xs font-medium uppercase text-slate-400">{titleize(key)}</p>
                        <p className="mt-1 truncate text-slate-700">{formatValue(value)}</p>
                      </div>
                    ))}
                </div>
              ))
            ) : (
              <p className="p-5 text-sm text-slate-500">No records yet.</p>
            )}
          </div>
        </div>
      ))}

      {!isLoading && !isError && !metrics.length && !sections.length ? <StateCard text="No module data yet." /> : null}

    </div>
  );
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function StateCard({ text, tone = "default" }: { text: string; tone?: "default" | "error" }) {
  return (
    <div className={`rounded-lg border p-5 text-sm shadow-sm ${tone === "error" ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-500"}`}>
      {text}
    </div>
  );
}
