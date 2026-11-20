const STOPS: [number, [number, number, number, number]][] = [
  [0, [37, 52, 148, 0]],
  [0.25, [44, 127, 184, 90]],
  [0.5, [65, 182, 196, 130]],
  [0.7, [254, 217, 118, 170]],
  [0.85, [253, 141, 60, 200]],
  [1, [227, 26, 28, 225]],
];

export function heatColor(level: number): [number, number, number, number] {
  const value = Math.min(1, Math.max(0, level));
  for (let index = 1; index < STOPS.length; index++) {
    const [position, color] = STOPS[index] as (typeof STOPS)[number];
    const [previous, from] = STOPS[index - 1] as (typeof STOPS)[number];
    if (value <= position) {
      const t = (value - previous) / (position - previous);
      return from.map((channel, i) =>
        Math.round(channel + ((color[i] as number) - channel) * t),
      ) as [number, number, number, number];
    }
  }
  return STOPS[STOPS.length - 1]?.[1] ?? [0, 0, 0, 0];
}

export function colorizeInPlace(pixels: Uint8ClampedArray) {
  for (let offset = 0; offset < pixels.length; offset += 4) {
    const [r, g, b, a] = heatColor((pixels[offset] ?? 0) / 255);
    pixels[offset] = r;
    pixels[offset + 1] = g;
    pixels[offset + 2] = b;
    pixels[offset + 3] = a;
  }
}
