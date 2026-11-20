import type { components } from "./schema";

export type Schemas = components["schemas"];
export type Site = Schemas["SiteOut"];
export type SiteInput = Schemas["SiteIn"];
export type Profile = Schemas["AnalysisProfile"];
export type Run = Schemas["RunOut"];
export type Page = Schemas["PageOut"];
export type Finding = Schemas["FindingOut"];
export type Report = Schemas["Report"];
export type Simulation = Schemas["SimulationOut"];

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const send = (method: string, body?: unknown): RequestInit => ({
  method,
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item: { loc?: unknown[]; msg?: string }) =>
          [item.loc?.slice(1).join("."), item.msg].filter(Boolean).join(": "),
        )
        .join("\n");
    }
  } catch {
    // fall through to the status text
  }
  return response.statusText || `Request failed (${response.status})`;
}
