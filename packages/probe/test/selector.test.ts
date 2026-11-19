import { beforeEach, describe, expect, it } from "vitest";
import { uniqueSelector, xpathOf } from "../src/selector";

beforeEach(() => {
  document.body.innerHTML = `
    <header><nav><a href="/">Home</a><a href="/about">About</a></nav></header>
    <main>
      <button id="buy">Buy</button>
      <button id="dup">One</button><button id="dup">Two</button>
      <section><p>First</p><p data-testid="second">Second</p><p class="note big">Third</p></section>
    </main>`;
});

const pick = (query: string, index = 0) => document.querySelectorAll(query)[index] as Element;

describe("uniqueSelector", () => {
  it.each([
    ["#buy", 0],
    ["nav a", 1],
    ["section p", 0],
    ["section p", 1],
    ["section p", 2],
    ["#dup", 1],
  ])("resolves back to the same element (%s #%i)", (query, index) => {
    const element = pick(query, index);
    const selector = uniqueSelector(element);
    expect(document.querySelectorAll(selector)).toHaveLength(1);
    expect(document.querySelector(selector)).toBe(element);
  });

  it("prefers ids and test ids", () => {
    expect(uniqueSelector(pick("#buy"))).toBe("#buy");
    expect(uniqueSelector(pick("[data-testid]"))).toBe('[data-testid="second"]');
  });
});

describe("xpathOf", () => {
  it("builds an indexed path", () => {
    expect(xpathOf(pick("nav a", 1))).toBe("/html/body/header/nav/a[2]");
  });
});
