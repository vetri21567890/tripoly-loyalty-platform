import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ugcApi } from "../api/services";

const UGC_TYPES = ["photo", "review_screenshot", "testimonial", "video", "reel"];

export default function UgcPage() {
  const [ugcType, setUgcType] = useState("photo");
  const [destination, setDestination] = useState("");
  const qc = useQueryClient();
  const { data: posts = [] } = useQuery({ queryKey: ["ugc"], queryFn: () => ugcApi.myPosts().then((r) => r.data.data) });

  const upload = useMutation({
    mutationFn: async () => {
      const init = await ugcApi.init(ugcType, destination || undefined);
      const threadId = init.data.data.ugc_thread_id as string;
      const objectKey = init.data.data.object_key as string;
      return ugcApi.complete(threadId, objectKey);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ugc"] });
      setDestination("");
      alert("Content submitted for review.");
    },
  });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <p className="eyebrow">UGC & Reviews</p>
        <h2 className="page-title">UGC Uploads</h2>
        <p className="page-subtitle">Submit travel photos, reviews, testimonials, reels, or videos for admin approval and coin rewards.</p>
      </section>

      <section className="max-w-2xl panel-card">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Content type</span>
            <select value={ugcType} onChange={(e) => setUgcType(e.target.value)} className="field">
              {UGC_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Destination or trip</span>
            <input value={destination} onChange={(e) => setDestination(e.target.value)} className="field" aria-label="Destination or trip" />
          </label>
        </div>
        <button onClick={() => upload.mutate()} disabled={upload.isPending} className="primary-button mt-5">
          Submit for Review
        </button>
        <p className="mt-3 text-xs text-slate-500">Coins are awarded only after admin approval. Rejected submissions can be reviewed and resubmitted.</p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <h3 className="font-semibold text-slate-950">Submission Status</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {posts.length ? (
            posts.map((post: any, index) => (
              <div key={`${post.created_at}-${index}`} className="grid gap-3 p-4 text-sm md:grid-cols-4">
                <span className="font-medium capitalize">{String(post.ugc_type).replace(/_/g, " ")}</span>
                <span className="capitalize">{String(post.status).replace(/_/g, " ")}</span>
                <span>{post.created_at ? new Date(String(post.created_at)).toLocaleString() : "-"}</span>
                <span className="text-red-600">{post.rejection_reason ?? ""}</span>
              </div>
            ))
          ) : (
            <p className="p-5 text-sm text-slate-500">No submissions yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}
