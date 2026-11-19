import { describe, expect, it } from "vitest";
import { blend, contrastRatio, parseColor } from "../src/color";

describe("parseColor", () => {
  it("reads rgb and rgba", () => {
    expect(parseColor("rgb(255, 0, 10)")).toEqual({ r: 255, g: 0, b: 10, a: 1 });
    expect(parseColor("rgba(0, 0, 0, 0.5)")).toEqual({ r: 0, g: 0, b: 0, a: 0.5 });
  });

  it("reads space separated syntax", () => {
    expect(parseColor("rgb(10 20 30 / 0.25)")).toEqual({ r: 10, g: 20, b: 30, a: 0.25 });
  });

  it("treats transparent and unknown values as null", () => {
    expect(parseColor("transparent")).toEqual({ r: 0, g: 0, b: 0, a: 0 });
    expect(parseColor("color(display-p3 1 0 0)")).toBeNull();
  });
});

describe("contrastRatio", () => {
  it("matches WCAG reference values", () => {
    const black = { r: 0, g: 0, b: 0, a: 1 };
    const white = { r: 255, g: 255, b: 255, a: 1 };
    expect(contrastRatio(black, white)).toBeCloseTo(21, 5);
    expect(contrastRatio(white, white)).toBeCloseTo(1, 5);
    expect(contrastRatio({ r: 118, g: 118, b: 118, a: 1 }, white)).toBeCloseTo(4.54, 2);
  });
});

describe("blend", () => {
  it("composites a translucent colour over its backdrop", () => {
    const result = blend({ r: 0, g: 0, b: 0, a: 0.5 }, { r: 255, g: 255, b: 255, a: 1 });
    expect(result.r).toBeCloseTo(127.5);
    expect(result.a).toBe(1);
  });
});
