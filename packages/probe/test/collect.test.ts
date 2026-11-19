import { beforeEach, describe, expect, it } from "vitest";
import { collect } from "../src/collect";

beforeEach(() => {
  document.documentElement.lang = "en";
  document.title = "Probe";
  document.body.innerHTML = `
    <h1>Homes</h1>
    <p>Plain copy</p>
    <a href="/about">About us</a>
    <div onclick="go()"><span>Clickable card</span></div>
    <img src="/a.png" alt="">
    <form action="/login" method="POST">
      <label for="email">Email</label><input id="email" name="email" type="email" required>
      <input name="password" type="password">
      <input type="hidden" name="csrf" value="x">
      <button>Sign in</button>
    </form>`;
});

describe("collect", () => {
  it("reports document metadata and headings", () => {
    const probe = collect();
    expect(probe.lang).toBe("en");
    expect(probe.title).toBe("Probe");
    expect(probe.headings).toEqual([{ level: 1, text: "Homes", selector: "h1" }]);
  });

  it("keeps interactive and text-bearing elements", () => {
    const probe = collect();
    const link = probe.elements.find((element) => element.tag === "a");
    expect(link).toMatchObject({ interactive: true, role: "link", name: "About us" });
    expect(probe.elements.some((element) => element.text === "Plain copy")).toBe(true);
    expect(probe.elements.some((element) => element.tag === "div" && element.interactive)).toBe(
      true,
    );
  });

  it("describes forms and flags sensitive fields", () => {
    const [form] = collect().forms;
    expect(form).toMatchObject({ action: "/login", method: "post", submitText: "Sign in" });
    expect(form?.fields.map((field) => [field.name, field.label, field.sensitive])).toEqual([
      ["email", "Email", false],
      ["password", null, true],
    ]);
  });

  it("lists images with their alt text", () => {
    expect(collect().images[0]).toMatchObject({ alt: "" });
  });
});
