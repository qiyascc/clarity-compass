import { blend, contrastRatio, parseColor, type Rgba, toCss } from "./color";
import {
  accessibleName,
  clean,
  documentBox,
  isInteractive,
  isVisible,
  labelFor,
  ownText,
  positionOf,
  roleOf,
} from "./dom";
import { uniqueSelector, xpathOf } from "./selector";
import type {
  Box,
  Heading,
  PageProbe,
  ProbedElement,
  ProbedField,
  ProbedForm,
  ProbedImage,
} from "./types";

const MAX_ELEMENTS = 2000;
const MAX_IMAGES = 300;
const WHITE: Rgba = { r: 255, g: 255, b: 255, a: 1 };
const SKIPPED_TAGS = new Set(["script", "style", "noscript", "template", "svg", "head", "meta"]);
const SENSITIVE_NAME = /pass|pwd|card|cvv|cvc|iban|ssn|secret|token|otp|pin/i;
const LANDMARKS: Record<string, string> = {
  header: "header, [role=banner]",
  nav: "nav, [role=navigation]",
  main: "main, [role=main]",
  footer: "footer, [role=contentinfo]",
  aside: "aside, [role=complementary]",
};

export function collect(): PageProbe {
  const { elements, truncated } = collectElements();
  return {
    url: location.href,
    title: document.title,
    lang: document.documentElement.getAttribute("lang"),
    viewportMeta: document.querySelector('meta[name="viewport"]')?.getAttribute("content") ?? null,
    viewport: { width: window.innerWidth, height: window.innerHeight },
    documentHeight: Math.max(
      document.documentElement.scrollHeight,
      document.body?.scrollHeight ?? 0,
    ),
    documentWidth: document.documentElement.scrollWidth,
    overflowing: collectOverflowing(),
    headings: collectHeadings(),
    elements,
    images: collectImages(),
    forms: collectForms(),
    landmarks: collectLandmarks(),
    truncated,
  };
}

function collectElements(): { elements: ProbedElement[]; truncated: boolean } {
  const elements: ProbedElement[] = [];
  const root = document.body;
  if (!root) return { elements, truncated: false };

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, {
    acceptNode: (node) =>
      SKIPPED_TAGS.has((node as Element).localName)
        ? NodeFilter.FILTER_REJECT
        : NodeFilter.FILTER_ACCEPT,
  });

  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const element = node as Element;
    const style = getComputedStyle(element);
    const interactive = isInteractive(element, style);
    const text = ownText(element);
    if (!interactive && !text) continue;
    if (elements.length >= MAX_ELEMENTS) return { elements, truncated: true };
    elements.push(describe(element, style, interactive, text, elements.length));
  }
  return { elements, truncated: false };
}

function describe(
  element: Element,
  style: CSSStyleDeclaration,
  interactive: boolean,
  text: string,
  index: number,
): ProbedElement {
  const box = documentBox(element);
  const foreground = parseColor(style.color);
  const backdrop = effectiveBackground(element);
  const contrast =
    foreground && backdrop.color && !backdrop.image
      ? Math.round(contrastRatio(foreground, backdrop.color) * 100) / 100
      : null;

  return {
    index,
    tag: element.localName,
    role: roleOf(element),
    name: interactive ? accessibleName(element) : "",
    text,
    selector: uniqueSelector(element),
    xpath: xpathOf(element),
    box,
    visible: isVisible(element, style, box),
    aboveFold: box.y < window.innerHeight,
    position: positionOf(style),
    interactive,
    href: element instanceof HTMLAnchorElement ? element.href || null : null,
    disabled: element.matches(":disabled") || element.getAttribute("aria-disabled") === "true",
    fontSize: Number.parseFloat(style.fontSize) || 0,
    fontWeight: Number.parseInt(style.fontWeight, 10) || 400,
    color: foreground ? toCss(foreground) : null,
    background: backdrop.color ? toCss(backdrop.color) : null,
    contrast,
    backgroundImage: backdrop.image,
  };
}

function effectiveBackground(element: Element): { color: Rgba | null; image: boolean } {
  const layers: Rgba[] = [];
  let image = false;
  for (let current: Element | null = element; current; current = current.parentElement) {
    const style = getComputedStyle(current);
    if (style.backgroundImage && style.backgroundImage !== "none") {
      image = true;
      break;
    }
    const color = parseColor(style.backgroundColor);
    if (color === null) return { color: null, image: false };
    if (color.a > 0) layers.push(color);
    if (color.a >= 1) break;
  }
  const base = layers.at(-1)?.a === 1 ? (layers.pop() as Rgba) : WHITE;
  const color = layers.reduceRight((under, layer) => blend(layer, under), base);
  return { color, image };
}

function collectOverflowing(): string[] {
  const limit = document.documentElement.clientWidth + 1;
  if (document.documentElement.scrollWidth <= limit) return [];
  const culprits: string[] = [];
  for (const element of document.body?.querySelectorAll("*") ?? []) {
    const rect = element.getBoundingClientRect();
    if (rect.right <= limit || rect.width === 0) continue;
    const parent = element.parentElement?.getBoundingClientRect();
    if (parent && parent.right > limit) continue;
    culprits.push(uniqueSelector(element));
    if (culprits.length >= 5) break;
  }
  return culprits;
}

function collectHeadings(): Heading[] {
  return [...document.querySelectorAll("h1, h2, h3, h4, h5, h6, [role=heading]")].map(
    (element) => ({
      level: Number(element.getAttribute("aria-level") ?? element.localName.slice(1)) || 2,
      text: clean(element.textContent ?? ""),
      selector: uniqueSelector(element),
    }),
  );
}

function collectImages(): ProbedImage[] {
  return [...document.querySelectorAll("img")].slice(0, MAX_IMAGES).map((image) => ({
    selector: uniqueSelector(image),
    src: image.currentSrc || image.src,
    alt: image.getAttribute("alt"),
    box: documentBox(image),
    loaded: image.complete && image.naturalWidth > 0,
    naturalWidth: image.naturalWidth,
    naturalHeight: image.naturalHeight,
    lazy: image.loading === "lazy",
  }));
}

function collectForms(): ProbedForm[] {
  return [...document.querySelectorAll("form")].map((form) => {
    const fields = [...form.elements]
      .filter(
        (field): field is HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement =>
          field instanceof HTMLInputElement ||
          field instanceof HTMLSelectElement ||
          field instanceof HTMLTextAreaElement,
      )
      .filter((field) => !["hidden", "submit", "button", "reset", "image"].includes(field.type))
      .map(describeField);
    const submit = form.querySelector("button:not([type=button]), input[type=submit]");
    return {
      selector: uniqueSelector(form),
      action: form.getAttribute("action"),
      method: (form.getAttribute("method") ?? "get").toLowerCase(),
      fields,
      submitText: submit ? accessibleName(submit) : null,
    };
  });
}

function describeField(
  field: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement,
): ProbedField {
  const autocomplete = field.getAttribute("autocomplete");
  const name = field.getAttribute("name");
  return {
    selector: uniqueSelector(field),
    tag: field.localName,
    type: field.type,
    name,
    label: labelFor(field),
    required: field.required || field.getAttribute("aria-required") === "true",
    autocomplete,
    sensitive:
      field.type === "password" ||
      Boolean(autocomplete?.startsWith("cc-")) ||
      SENSITIVE_NAME.test(`${name ?? ""} ${field.id}`),
    box: documentBox(field),
  };
}

function collectLandmarks(): Record<string, Box[]> {
  const result: Record<string, Box[]> = {};
  for (const [name, query] of Object.entries(LANDMARKS)) {
    const boxes = [...document.querySelectorAll(query)].map(documentBox);
    if (boxes.length) result[name] = boxes;
  }
  return result;
}
