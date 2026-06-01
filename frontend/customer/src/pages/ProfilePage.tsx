import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "../api/services";

export default function ProfilePage() {
  const qc = useQueryClient();
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: () => profileApi.get().then((r) => r.data.data as Record<string, unknown>) });
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const update = useMutation({
    mutationFn: () => profileApi.update({ first_name: firstName || String(profile?.first_name || ""), last_name: lastName }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
  });

  const complete = useMutation({
    mutationFn: () => profileApi.complete().then((r) => r.data.data),
    onSuccess: (d) => {
      alert(`Profile completed! +${d.coins_awarded} coins`);
      qc.invalidateQueries({ queryKey: ["wallet"] });
    },
  });

  return (
    <div className="page-shell max-w-2xl">
      <section className="page-hero">
        <p className="eyebrow">Customer Profile</p>
        <h2 className="page-title">Profile</h2>
        <p className="page-subtitle">Keep your travel loyalty profile updated to unlock missions and personalized campaign eligibility.</p>
      </section>
      <div className="panel-card space-y-4">
        <input
          aria-label="First name"
          defaultValue={String(profile?.first_name || "")}
          onChange={(e) => setFirstName(e.target.value)}
          className="field"
        />
        <input
          aria-label="Last name"
          defaultValue={String(profile?.last_name || "")}
          onChange={(e) => setLastName(e.target.value)}
          className="field"
        />
        <button onClick={() => update.mutate()} className="primary-button w-full">
          Save Profile
        </button>
        {!profile?.profile_completed_at && (
          <button onClick={() => complete.mutate()} className="secondary-button w-full">
            Complete Profile (+50 Coins)
          </button>
        )}
      </div>
    </div>
  );
}
