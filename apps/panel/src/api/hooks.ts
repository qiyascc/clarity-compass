import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  api,
  type Finding,
  type Page,
  type Report,
  type Run,
  type Site,
  type SiteInput,
  send,
} from "./client";

export const keys = {
  me: ["me"] as const,
  sites: ["sites"] as const,
  site: (id: string) => ["sites", id] as const,
  runs: (siteId: string) => ["sites", siteId, "runs"] as const,
  run: (id: string) => ["runs", id] as const,
  pages: (runId: string) => ["runs", runId, "pages"] as const,
  findings: (runId: string) => ["runs", runId, "findings"] as const,
  report: (runId: string) => ["runs", runId, "report"] as const,
};

const ACTIVE = new Set(["queued", "running"]);
const isActive = (run?: Run) => Boolean(run && ACTIVE.has(run.status));

export const useMe = () =>
  useQuery({
    queryKey: keys.me,
    queryFn: () => api<{ username: string }>("/auth/me"),
    retry: false,
  });

export function useLogin() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: { username: string; password: string }) =>
      api<void>("/auth/login", send("POST", body)),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.me }),
  });
}

export function useLogout() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api<void>("/auth/logout", send("POST")),
    onSuccess: () => client.clear(),
  });
}

export const useSites = () =>
  useQuery({ queryKey: keys.sites, queryFn: () => api<Site[]>("/sites") });

export const useSite = (id: string) =>
  useQuery({ queryKey: keys.site(id), queryFn: () => api<Site>(`/sites/${id}`) });

export function useCreateSite() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: SiteInput) => api<Site>("/sites", send("POST", body)),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.sites }),
  });
}

export function useUpdateSite(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<SiteInput>) => api<Site>(`/sites/${id}`, send("PATCH", body)),
    onSuccess: (site) => {
      client.setQueryData(keys.site(id), site);
      client.invalidateQueries({ queryKey: keys.sites });
    },
  });
}

export function useDeleteSite() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api<void>(`/sites/${id}`, send("DELETE")),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.sites }),
  });
}

export function useSiteSecrets(id: string) {
  const client = useQueryClient();
  const refresh = () => client.invalidateQueries({ queryKey: keys.site(id) });
  return {
    saveCredentials: useMutation({
      mutationFn: (body: {
        login_url: string;
        username: string;
        password: string;
        username_selector: string | null;
        password_selector: string | null;
        submit_selector: string | null;
      }) => api<void>(`/sites/${id}/credentials`, send("PUT", body)),
      onSuccess: refresh,
    }),
    clearCredentials: useMutation({
      mutationFn: () => api<void>(`/sites/${id}/credentials`, send("DELETE")),
      onSuccess: refresh,
    }),
    rotateKey: useMutation({
      mutationFn: () => api<{ key: string }>(`/sites/${id}/extension-key`, send("POST")),
      onSuccess: refresh,
    }),
    revokeKey: useMutation({
      mutationFn: () => api<void>(`/sites/${id}/extension-key`, send("DELETE")),
      onSuccess: refresh,
    }),
  };
}

export const useRuns = (siteId: string) =>
  useQuery({
    queryKey: keys.runs(siteId),
    queryFn: () => api<Run[]>(`/sites/${siteId}/runs`),
    refetchInterval: (query) => (query.state.data?.some(isActive) ? 3000 : false),
  });

export function useStartRun(siteId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api<Run>(`/sites/${siteId}/runs`, send("POST")),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.runs(siteId) }),
  });
}

export const useRun = (id: string) =>
  useQuery({
    queryKey: keys.run(id),
    queryFn: () => api<Run>(`/runs/${id}`),
    refetchInterval: (query) => (isActive(query.state.data) ? 2000 : false),
  });

export function useCancelRun(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api<Run>(`/runs/${id}/cancel`, send("POST")),
    onSuccess: (run) => client.setQueryData(keys.run(id), run),
  });
}

export const usePages = (runId: string, live: boolean) =>
  useQuery({
    queryKey: keys.pages(runId),
    queryFn: () => api<Page[]>(`/runs/${runId}/pages`),
    refetchInterval: live ? 3000 : false,
  });

export const useFindings = (runId: string) =>
  useQuery({
    queryKey: keys.findings(runId),
    queryFn: () => api<Finding[]>(`/runs/${runId}/findings`),
  });

export { isActive };

export const useReport = (runId: string) =>
  useQuery({
    queryKey: keys.report(runId),
    queryFn: () => api<Report>(`/runs/${runId}/report`),
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 2,
  });
