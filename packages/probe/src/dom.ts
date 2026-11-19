import type { Box, Position } from "./types";

const IMPLICIT_ROLES: Record<string, string> = {
  a: "link",
  button: "button",
  select: "combobox",
  textarea: "textbox",
  nav: "navigation",
  main: "main",
  header: "banner",
  footer: "contentinfo",
  form: "form",
  img: "img",
  summary: "button",
  h1: "heading",
  h2: "heading",
  h3: "heading",
  h4: "heading",
  h5: "heading",
  h6: "heading",
};

const INPUT_ROLES: Record<string, string> = {
  button: "button",
  submit: "button",
  reset: "button",
  checkbox: "checkbox",
  radio: "radio",
  range: "slider",
  search: "searchbox",
};

// biome-ignore format: compact list
const INTERACTIVE_ROLES = new Set([
  "button", "link", "checkbox", "radio", "switch", "tab", "menuitem", "option",
  "combobox", "textbox", "searchbox", "slider",
]);

export function documentBox(element: Element): Box {
  const rect = element.getBoundingClientRect();
  return {
    x: Math.round(rect.left + window.scrollX),
    y: Math.round(rect.top + window.scrollY),
    width: Math.round(rect.width),
    height: Math.round(rect.height),
  };
}

export function isVisible(element: Element, style: CSSStyleDeclaration, box: Box): boolean {
  if (box.width < 1 || box.height < 1) return false;
  if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse")
    return false;
  if (Number(style.opacity) === 0) return false;
  return element.checkVisibility?.({ checkOpacity: true, checkVisibilityCSS: true }) ?? true;
}

export function roleOf(element: Element): string | null {
  const explicit = element.getAttribute("role");
  if (explicit) return explicit.split(/\s+/)[0] ?? null;
  const tag = element.localName;
  if (tag === "a" && !element.hasAttribute("href")) return null;
  if (tag === "input") return INPUT_ROLES[(element as HTMLInputElement).type] ?? "textbox";
  return IMPLICIT_ROLES[tag] ?? null;
}

export function isInteractive(element: Element, style: CSSStyleDeclaration): boolean {
  const tag = element.localName;
  if (tag === "a") return element.hasAttribute("href");
  if (["button", "input", "select", "textarea", "summary"].includes(tag)) return true;
  const role = element.getAttribute("role");
  if (role && INTERACTIVE_ROLES.has(role)) return true;
  if (element.hasAttribute("onclick")) return true;
  const tabindex = element.getAttribute("tabindex");
  if (tabindex !== null && Number(tabindex) >= 0) return true;
  if (style.cursor === "pointer") {
    const parent = element.parentElement;
    return !parent || getComputedStyle(parent).cursor !== "pointer";
  }
  return false;
}

export function accessibleName(element: Element): string {
  const label = element.getAttribute("aria-label");
  if (label?.trim()) return clean(label);
  const labelledBy = element.getAttribute("aria-labelledby");
  if (labelledBy) {
    const text = labelledBy
      .split(/\s+/)
      .map((id) => document.getElementById(id)?.textContent ?? "")
      .join(" ");
    if (text.trim()) return clean(text);
  }
  if (element instanceof HTMLImageElement) return clean(element.alt);
  if (
    element instanceof HTMLInputElement ||
    element instanceof HTMLSelectElement ||
    element instanceof HTMLTextAreaElement
  ) {
    const fieldLabel = labelFor(element);
    if (fieldLabel) return fieldLabel;
    if (element instanceof HTMLInputElement && ["submit", "button"].includes(element.type))
      return clean(element.value);
    return clean(element.getAttribute("placeholder") ?? "");
  }
  // biome-ignore lint/performance/useDomNodeTextContent: rendered text skips hidden content
  const text = clean((element as HTMLElement).innerText ?? element.textContent ?? "");
  if (text) return text;
  const imageAlt = element.querySelector("img[alt]")?.getAttribute("alt");
  if (imageAlt) return clean(imageAlt);
  return clean(element.getAttribute("title") ?? "");
}

export function labelFor(
  field: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement,
): string | null {
  const text = [...(field.labels ?? [])].map((label) => label.textContent ?? "").join(" ");
  return text.trim() ? clean(text) : null;
}

export function ownText(element: Element): string {
  let text = "";
  for (const node of element.childNodes) {
    if (node.nodeType === Node.TEXT_NODE) text += node.textContent ?? "";
  }
  return clean(text);
}

export function positionOf(style: CSSStyleDeclaration): Position {
  const value = style.position;
  return value === "fixed" || value === "sticky" || value === "absolute" || value === "relative"
    ? value
    : "static";
}

export function clean(text: string, limit = 160): string {
  const collapsed = text.replace(/\s+/g, " ").trim();
  return collapsed.length > limit ? `${collapsed.slice(0, limit - 1)}…` : collapsed;
}
