import { api, ApiResponse } from "./client";

export const authApi = {
  signup: (email: string, password: string, first_name?: string, last_name?: string) =>
    api.post<ApiResponse<{ access_token: string; refresh_token: string; expires_in_seconds: number }>>(
      "/auth/signup",
      { email, password, first_name, last_name }
    ),
  signin: (email: string, password: string) =>
    api.post<ApiResponse<{ access_token: string; refresh_token: string; expires_in_seconds: number }>>(
      "/auth/signin",
      { email, password }
    ),
  me: () => api.get<ApiResponse<{ id: string; phone: string | null; email: string | null; status: string }>>("/auth/me"),
};

export const walletApi = {
  balance: () =>
    api.get<
      ApiResponse<{
        available_coins: number;
        expired_coins: number;
        lifetime_coins_earned: number;
        redeemed_coins_to_date: number;
        approx_redemption_value_inr: number;
        coins_per_rupee: number;
        conversion_rule: string;
      }>
    >("/wallet/balance"),
  transactions: (limit = 20) =>
    api.get<ApiResponse<Array<{ transaction_id: string; direction: string; amount: number; reason_code: string; created_at: string }>>>(
      "/wallet/transactions",
      { params: { limit } }
    ),
  expiringSoon: (days = 30, limit = 5) =>
    api.get<
      ApiResponse<{
        days: number;
        total_amount_remaining: number;
        grants: Array<{
          coin_grant_id: string;
          earned_date: string;
          expiry_date: string | null;
          amount_remaining: number;
          amount_total: number;
          status: string;
          grant_source: string;
        }>;
      }>
    >("/wallet/expiring-soon", { params: { days, limit } }),
};

export const tierApi = {
  current: () =>
    api.get<ApiResponse<{ tier_code: string; tier_name: string; lifetime_coins_earned: number }>>("/tiers/current"),
};

export const referralApi = {
  me: () =>
    api.get<ApiResponse<{ referral_code: string; referral_link: string; status_summary: Record<string, number> }>>(
      "/referrals/me"
    ),
  status: () => api.get<ApiResponse<Array<{ referral_attribution_id: string; status: string }>>>("/referrals/status"),
};

export const rewardsApi = {
  catalog: () =>
    api.get<
      ApiResponse<
        Array<{
          reward_catalog_id: string;
          title: string;
          cost_coins: number;
          approx_value_inr?: number | null;
          unlimited_inventory: boolean;
          inventory_remaining: number | null;
        }>
      >
    >("/rewards/catalog"),
  redeem: (reward_catalog_id: string, idempotencyKey: string) =>
    api.post<
      ApiResponse<{ reward_redemption_id: string; coins_spent: number; redeemed_at: string; voucher_code?: string | null }>
    >(
      "/rewards/redemptions",
      { reward_catalog_id },
      { headers: { "Idempotency-Key": idempotencyKey } }
    ),
  history: (limit = 20) =>
    api.get<ApiResponse<Array<Record<string, unknown>>>>("/rewards/redemptions/history", { params: { limit } }),
};

export const profileApi = {
  get: () => api.get<ApiResponse<Record<string, unknown>>>("/customers/me/profile"),
  update: (data: { first_name: string; last_name?: string; birthday?: string }) =>
    api.put("/customers/me/profile", data),
  complete: () => api.post<ApiResponse<{ profile_completed: boolean; coins_awarded: number }>>("/customers/me/complete-profile"),
};

export const ugcApi = {
  init: (ugc_type: string, destination?: string) =>
    api.post<ApiResponse<Record<string, unknown>>>("/ugc/upload/init", { ugc_type, destination }),
  complete: (ugc_thread_id: string, media_object_key: string) =>
    api.post("/ugc/upload/complete", { ugc_thread_id, media_object_key, content_metadata: {} }),
  myPosts: () => api.get<ApiResponse<Array<Record<string, unknown>>>>("/ugc/my-posts"),
};

export const missionsApi = {
  available: () => api.get<ApiResponse<Array<{ mission_code: string; title: string; coins_awarded: number }>>>("/missions/available"),
  progress: () => api.get<ApiResponse<Array<{ mission_code: string; status: string; coins_awarded: number | null }>>>("/missions/progress"),
};

export const campaignsApi = {
  list: () => api.get<ApiResponse<Array<Record<string, unknown>>>>("/campaigns/list"),
  enroll: (campaignId: string) => api.post(`/campaigns/${campaignId}/enroll`),
};

export const notificationsApi = {
  inbox: () => api.get<ApiResponse<Array<{ id: string; title: string; body: string | null; read_at: string | null }>>>("/notifications/inbox"),
  unreadCount: () => api.get<ApiResponse<{ unread_count: number }>>("/notifications/unread-count"),
  markRead: (id: string) => api.post(`/notifications/${id}/read`),
};
