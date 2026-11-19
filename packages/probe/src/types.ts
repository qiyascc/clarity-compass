export interface Box {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type Position = "static" | "relative" | "absolute" | "fixed" | "sticky";

export interface ProbedElement {
  index: number;
  tag: string;
  role: string | null;
  name: string;
  text: string;
  selector: string;
  xpath: string;
  box: Box;
  visible: boolean;
  aboveFold: boolean;
  position: Position;
  interactive: boolean;
  href: string | null;
  disabled: boolean;
  fontSize: number;
  fontWeight: number;
  color: string | null;
  background: string | null;
  contrast: number | null;
  backgroundImage: boolean;
}

export interface ProbedImage {
  selector: string;
  src: string;
  alt: string | null;
  box: Box;
  loaded: boolean;
  naturalWidth: number;
  naturalHeight: number;
  lazy: boolean;
}

export interface ProbedField {
  selector: string;
  tag: string;
  type: string;
  name: string | null;
  label: string | null;
  required: boolean;
  autocomplete: string | null;
  sensitive: boolean;
  box: Box;
}

export interface ProbedForm {
  selector: string;
  action: string | null;
  method: string;
  fields: ProbedField[];
  submitText: string | null;
}

export interface Heading {
  level: number;
  text: string;
  selector: string;
}

export interface PageProbe {
  url: string;
  title: string;
  lang: string | null;
  viewportMeta: string | null;
  viewport: { width: number; height: number };
  documentHeight: number;
  headings: Heading[];
  elements: ProbedElement[];
  images: ProbedImage[];
  forms: ProbedForm[];
  landmarks: Record<string, Box[]>;
  truncated: boolean;
}
