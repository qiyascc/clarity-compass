export interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

const RGB = /^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/;

export function parseColor(value: string): Rgba | null {
  if (value === "transparent") return { r: 0, g: 0, b: 0, a: 0 };
  const match = RGB.exec(value.trim());
  if (!match) return null;
  const [, r, g, b, alpha] = match;
  return {
    r: Number(r),
    g: Number(g),
    b: Number(b),
    a:
      alpha === undefined
        ? 1
        : alpha.endsWith("%")
          ? Number.parseFloat(alpha) / 100
          : Number(alpha),
  };
}

export function blend(top: Rgba, bottom: Rgba): Rgba {
  const a = top.a + bottom.a * (1 - top.a);
  if (a === 0) return { r: 0, g: 0, b: 0, a: 0 };
  const mix = (t: number, u: number) => (t * top.a + u * bottom.a * (1 - top.a)) / a;
  return { r: mix(top.r, bottom.r), g: mix(top.g, bottom.g), b: mix(top.b, bottom.b), a };
}

export function luminance({ r, g, b }: Rgba): number {
  const channel = (value: number) => {
    const c = value / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

export function contrastRatio(foreground: Rgba, background: Rgba): number {
  const fg = luminance(blend(foreground, background));
  const bg = luminance(background);
  const [light, dark] = fg > bg ? [fg, bg] : [bg, fg];
  return (light + 0.05) / (dark + 0.05);
}

export function toCss({ r, g, b, a }: Rgba): string {
  const round = (n: number) => Math.round(n);
  return a === 1
    ? `rgb(${round(r)}, ${round(g)}, ${round(b)})`
    : `rgba(${round(r)}, ${round(g)}, ${round(b)}, ${Number(a.toFixed(3))})`;
}
