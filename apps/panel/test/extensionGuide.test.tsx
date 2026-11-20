import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";
import { EXTENSION_DOWNLOAD, ExtensionGuide } from "@/routes/ExtensionGuide";

describe("ExtensionGuide", () => {
  it("offers the download and the address to enter in the extension", () => {
    const router = createMemoryRouter([{ path: "/", element: <ExtensionGuide /> }]);
    render(<RouterProvider router={router} />);
    const download = screen.getByRole("link", { name: /download/i });
    expect(download.getAttribute("href")).toBe(EXTENSION_DOWNLOAD);
    expect(screen.getByText("chrome://extensions")).toBeTruthy();
    expect(screen.getByText(window.location.host)).toBeTruthy();
  });
});
