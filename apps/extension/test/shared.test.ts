import { describe, expect, it } from "vitest";
import { belongsToSite, normaliseApiBase, siteOrigins, viewportFor } from "../src/shared";

describe("shared helpers", () => {
  it("normalises the API base to an origin", () => {
    expect(normaliseApiBase(" clarity.example.com/ ")).toBe("https://clarity.example.com");
    expect(normaliseApiBase("http://127.0.0.1:8765/api/")).toBe("http://127.0.0.1:8765");
  });

  it("collects every origin the site was seen on, with and without www", () => {
    const origins = siteOrigins({
      name: "Qiyas",
      start_url: "https://theqiyas.cc/",
      run_id: "r",
      pages: [
        {
          id: "p",
          url: "https://theqiyas.cc/",
          final_url: "https://qiyas.cc/",
          viewport: "desktop",
        },
      ],
    });
    expect(origins).toEqual([
      "https://qiyas.cc",
      "https://theqiyas.cc",
      "https://www.qiyas.cc",
      "https://www.theqiyas.cc",
    ]);
    expect(belongsToSite("https://www.qiyas.cc/about", origins)).toBe(true);
    expect(belongsToSite("https://evil.test/", origins)).toBe(false);
  });

  it("picks the analysed viewport closest to the window", () => {
    expect(viewportFor(390)).toBe("mobile");
    expect(viewportFor(834)).toBe("tablet");
    expect(viewportFor(1440)).toBe("desktop");
  });
});
