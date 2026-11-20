import { describe, expect, it } from "vitest";
import { colorizeInPlace, heatColor } from "@/components/heat";

describe("heatColor", () => {
  it("is transparent at zero and opaque red at the peak", () => {
    expect(heatColor(0)[3]).toBe(0);
    expect(heatColor(1)).toEqual([227, 26, 28, 225]);
  });

  it("interpolates between stops and clamps", () => {
    expect(heatColor(0.125)).toEqual([41, 90, 166, 45]);
    expect(heatColor(4)).toEqual(heatColor(1));
  });

  it("colorizes grey pixels in place", () => {
    const pixels = new Uint8ClampedArray([255, 255, 255, 255, 0, 0, 0, 255]);
    colorizeInPlace(pixels);
    expect([...pixels.slice(0, 4)]).toEqual([227, 26, 28, 225]);
    expect(pixels[7]).toBe(0);
  });
});
