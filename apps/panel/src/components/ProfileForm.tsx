import { type FormEvent, useState } from "react";
import {
  emptyProfile,
  LANGUAGES,
  type Language,
  type ProfileValues,
  type Scope,
  VIEWPORTS,
  type ViewportName,
} from "./profile";
import { Button, Field, Input, Select, TextArea } from "./ui";

interface Props {
  initial?: ProfileValues;
  name?: string;
  submitLabel: string;
  busy?: boolean;
  onSubmit: (name: string, values: ProfileValues) => void;
}

const SCOPES: { value: Scope; label: string; hint: string }[] = [
  { value: "site", label: "Whole site", hint: "Follow links and the sitemap within the limits" },
  { value: "pages", label: "Selected pages", hint: "Only the URLs listed below" },
  { value: "single", label: "Single page", hint: "Only the start URL" },
];

export function ProfileForm({
  initial = emptyProfile,
  name = "",
  submitLabel,
  busy,
  onSubmit,
}: Props) {
  const [siteName, setSiteName] = useState(name);
  const [values, setValues] = useState(initial);
  const set = <K extends keyof ProfileValues>(key: K, value: ProfileValues[K]) =>
    setValues((current) => ({ ...current, [key]: value }));

  const toggleViewport = (viewport: ViewportName) =>
    set(
      "viewports",
      values.viewports.includes(viewport)
        ? values.viewports.filter((item) => item !== viewport)
        : [...values.viewports, viewport],
    );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(siteName.trim(), values);
  };

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name">
          <Input
            required
            value={siteName}
            onChange={(e) => setSiteName(e.target.value)}
            placeholder="Qiyas CC"
          />
        </Field>
        <Field label="Start URL">
          <Input
            required
            value={values.startUrl}
            onChange={(e) => set("startUrl", e.target.value)}
            placeholder="theqiyas.cc"
          />
        </Field>
      </div>

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium">Scope</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {SCOPES.map((scope) => (
            <label
              key={scope.value}
              className={`cursor-pointer rounded-md border p-3 text-sm transition ${values.scope === scope.value ? "border-accent bg-accent-soft" : "border-line bg-white hover:border-ink-faint"}`}
            >
              <input
                type="radio"
                name="scope"
                className="sr-only"
                checked={values.scope === scope.value}
                onChange={() => set("scope", scope.value)}
              />
              <span className="block font-medium">{scope.label}</span>
              <span className="block text-xs text-ink-soft">{scope.hint}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {values.scope === "pages" && (
        <Field label="Pages" hint="One URL per line, all on the same site">
          <TextArea rows={4} value={values.pages} onChange={(e) => set("pages", e.target.value)} />
        </Field>
      )}

      <div className="grid gap-4 sm:grid-cols-4">
        <Field label="Notes language">
          <Select
            value={values.language}
            onChange={(e) => set("language", e.target.value as Language)}
          >
            {Object.entries(LANGUAGES).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Max pages">
          <Input
            type="number"
            min={1}
            max={500}
            value={values.maxPages}
            disabled={values.scope !== "site"}
            onChange={(e) => set("maxPages", Number(e.target.value))}
          />
        </Field>
        <Field label="Max depth">
          <Input
            type="number"
            min={0}
            max={10}
            value={values.maxDepth}
            disabled={values.scope !== "site"}
            onChange={(e) => set("maxDepth", Number(e.target.value))}
          />
        </Field>
        <fieldset className="space-y-1.5">
          <legend className="text-sm font-medium">Viewports</legend>
          <div className="flex gap-3 pt-1.5">
            {VIEWPORTS.map((viewport) => (
              <label key={viewport} className="flex items-center gap-1.5 text-sm capitalize">
                <input
                  type="checkbox"
                  className="accent-accent"
                  checked={values.viewports.includes(viewport)}
                  onChange={() => toggleViewport(viewport)}
                />
                {viewport}
              </label>
            ))}
          </div>
        </fieldset>
      </div>

      {values.scope === "site" && (
        <Field label="Exclude paths" hint="Glob patterns, one per line, e.g. /admin/*">
          <TextArea
            rows={2}
            value={values.exclude}
            onChange={(e) => set("exclude", e.target.value)}
          />
        </Field>
      )}

      <Button type="submit" tone="primary" disabled={busy || values.viewports.length === 0}>
        {submitLabel}
      </Button>
    </form>
  );
}
