import { describe, expect, it } from "vitest";
import { emptyProfile, fromProfile, toProfile } from "@/components/profile";

describe("toProfile", () => {
  it("only sends selected pages for the pages scope", () => {
    const site = toProfile({ ...emptyProfile, startUrl: " theqiyas.cc ", pages: "/a\n/b" });
    expect(site.start_url).toBe("theqiyas.cc");
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
      startUrl: "https://theqiyas.cc/",
      scope: "pages" as const,
      pages: "https://theqiyas.cc/about",
      exclude: "/admin/*",
      language: "az" as const,
      maxPages: 5,
      maxDepth: 1,
    };
    expect(fromProfile(toProfile(values))).toEqual(values);
  });
});
