// Helpers around the browser storage keys the UdyamAI frontend uses to
// remember the signed-in user and their linked profile.

export const STORAGE_KEYS = {
  user: 'udyam_user', // phone (10 digits, without +91)
  profileId: 'udyam_profile_id',
  profile: 'udyam_profile',
  analysisInputs: 'udyam_analysis_inputs',
  activeAnalysisId: 'udyam_active_analysis_id',
} as const;

export function hasWindowStorage(): boolean {
  return typeof window !== 'undefined';
}

/** Persist the Supabase user's phone in the legacy storage key. */
export function storeUserPhone(phone?: string | null) {
  if (!hasWindowStorage()) return;
  if (!phone) {
    window.sessionStorage.removeItem(STORAGE_KEYS.user);
    return;
  }
  // Supabase stores E.164 (e.g. +919876543210); the UI expects 10 digits.
  const digits = phone.replace(/\D/g, '').slice(-10);
  window.sessionStorage.setItem(STORAGE_KEYS.user, digits);
}

export function storeProfile(profile: { id: string; name?: string | null } | null) {
  if (!hasWindowStorage()) return;
  if (!profile) {
    window.localStorage.removeItem(STORAGE_KEYS.profileId);
    window.localStorage.removeItem(STORAGE_KEYS.profile);
    window.sessionStorage.removeItem(STORAGE_KEYS.profileId);
    return;
  }
  window.localStorage.setItem(STORAGE_KEYS.profileId, String(profile.id));
  window.sessionStorage.setItem(STORAGE_KEYS.profileId, String(profile.id));
  window.localStorage.setItem(STORAGE_KEYS.profile, JSON.stringify(profile));
}

export function readProfileId(): string | null {
  if (!hasWindowStorage()) return null;
  return (
    window.localStorage.getItem(STORAGE_KEYS.profileId) ||
    window.sessionStorage.getItem(STORAGE_KEYS.profileId)
  );
}

/** Clear every auth/demo storage key (used on sign out). */
export function clearAuthStorage() {
  if (!hasWindowStorage()) return;
  const values = Object.values(STORAGE_KEYS);
  values.forEach((key) => {
    window.localStorage.removeItem(key);
    window.sessionStorage.removeItem(key);
  });
}
