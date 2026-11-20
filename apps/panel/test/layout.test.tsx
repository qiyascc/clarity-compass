import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { REPOSITORY } from "@/routes/Landing";
import { Layout } from "@/routes/Layout";

const respond = (status: number, body: unknown) =>
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );

const renderAt = (path: string) => {
  const router = createMemoryRouter(
    [
      { path: "/login", element: <p>login form</p> },
      {
        element: <Layout />,
        children: [
          { index: true, element: <p>sites</p> },
          { path: "sites/:siteId", element: <p>site</p> },
        ],
      },
    ],
    { initialEntries: [path] },
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
};

describe("Layout", () => {
  afterEach(() => vi.restoreAllMocks());

  it("shows visitors the public page with a link to the repository", async () => {
    respond(401, { detail: "not signed in" });
    renderAt("/");
    const link = await screen.findByRole("link", { name: /github/i });
    expect(link.getAttribute("href")).toBe(REPOSITORY);
    expect(screen.queryByText("sites")).toBeNull();
  });

  it("sends visitors on admin pages to the sign-in form", async () => {
    respond(401, { detail: "not signed in" });
    renderAt("/sites/abc");
    expect(await screen.findByText("login form")).toBeTruthy();
  });

  it("shows the admin area once signed in", async () => {
    respond(200, { username: "qiyascc" });
    renderAt("/");
    expect(await screen.findByText("sites")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /github/i })).toBeNull();
  });
});
