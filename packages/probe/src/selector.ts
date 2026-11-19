const TEST_ATTRIBUTES = ["data-testid", "data-test", "data-qa", "data-cy"];
const MAX_DEPTH = 12;

export function uniqueSelector(element: Element): string {
  const own = stableHandle(element);
  if (own && isUnique(own)) return own;

  const parts: string[] = [];
  let current: Element | null = element;
  while (current && current !== document.documentElement && parts.length < MAX_DEPTH) {
    const handle = stableHandle(current);
    if (handle && isUnique(handle)) {
      parts.unshift(handle);
      break;
    }
    parts.unshift(step(current));
    const candidate = parts.join(" > ");
    if (isUnique(candidate) && document.querySelector(candidate) === element) return candidate;
    current = current.parentElement;
  }
  return parts.join(" > ");
}

export function xpathOf(element: Element): string {
  const segments: string[] = [];
  let current: Element | null = element;
  while (current) {
    const tag = current.localName;
    const parent: Element | null = current.parentElement;
    if (!parent) {
      segments.unshift(tag);
      break;
    }
    const siblings = [...parent.children].filter((child) => child.localName === tag);
    segments.unshift(siblings.length > 1 ? `${tag}[${siblings.indexOf(current) + 1}]` : tag);
    current = parent;
  }
  return `/${segments.join("/")}`;
}

function stableHandle(element: Element): string | null {
  if (element.id && /^[A-Za-z][\w-]*$/.test(element.id)) return `#${element.id}`;
  for (const attribute of TEST_ATTRIBUTES) {
    const value = element.getAttribute(attribute);
    if (value) return `[${attribute}="${CSS.escape(value)}"]`;
  }
  return null;
}

function step(element: Element): string {
  const tag = element.localName;
  const parent = element.parentElement;
  if (!parent) return tag;
  const sameTag = [...parent.children].filter((child) => child.localName === tag);
  return sameTag.length === 1 ? tag : `${tag}:nth-of-type(${sameTag.indexOf(element) + 1})`;
}

function isUnique(selector: string): boolean {
  try {
    return document.querySelectorAll(selector).length === 1;
  } catch {
    return false;
  }
}
