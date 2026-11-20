import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";
import { Replay } from "./replay/Replay";
import { Layout } from "./routes/Layout";
import { Login } from "./routes/Login";
import { ReportView } from "./routes/ReportView";
import { RunDetail } from "./routes/RunDetail";
import { SiteDetail } from "./routes/SiteDetail";
import { Sites } from "./routes/Sites";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5_000, refetchOnWindowFocus: false } },
});

const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  {
    element: <Layout />,
    children: [
      { index: true, element: <Sites /> },
      { path: "sites/:siteId", element: <SiteDetail /> },
      { path: "runs/:runId", element: <RunDetail /> },
      { path: "runs/:runId/pages/:pageId", element: <Replay /> },
      { path: "runs/:runId/report", element: <ReportView /> },
    ],
  },
]);

const root = document.getElementById("root");
if (!root) throw new Error("missing #root");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
