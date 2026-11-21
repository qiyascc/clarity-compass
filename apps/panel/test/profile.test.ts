import { describe, expect, it } from "vitest";
import { emptyProfile, fromProfile, toProfile } from "@/components/profile";

describe("toProfile", () => {
  it("only sends selected pages for the pages scope", () => {
    const site = toProfile({ ...emptyProfile, startUrl: " example.com ", pages: "/a\n/b" });
    expect(site.start_url).toBe("example.com");
    expect(site.pages).toEqual([]);

    const pages = toProfile({ ...emptyProfile, scope: "pages", pages: " /a \n\n/b\n" });
    expect(pages.pages).toEqual(["/a", "/b"]);
  });

  it("keeps viewports in canonical order", () => {
    const profile = toProfile({ ...emptyProfile, viewports: ["mobile", "desktop"] });
    expect(profile.viewports).toEqual(["desktop", "mobile"]);
  });

  it("round-trips through fromProfile", () => {
    const values = {
      ...emptyProfile,
      startUrl: "https://example.com/",
      scope: "pages" as const,
      pages: "https://example.com/about",
      exclude: "/admin/*",
      language: "az" as const,
      maxPages: 5,
      maxDepth: 1,
    };
    expect(fromProfile(toProfile(values))).toEqual(values);
  });
});
