import { type FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import {
  useDeleteSite,
  useRuns,
  useSite,
  useSiteSecrets,
  useStartRun,
  useUpdateSite,
} from "@/api/hooks";
import { CopyField } from "@/components/CopyButton";
import { ProfileForm } from "@/components/ProfileForm";
import { fromProfile, toProfile } from "@/components/profile";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, Card, ErrorText, Field, Input } from "@/components/ui";
import { formatDate } from "@/format";

export function SiteDetail() {
  const { siteId = "" } = useParams();
  const site = useSite(siteId);
  const runs = useRuns(siteId);
  const start = useStartRun(siteId);
  const update = useUpdateSite(siteId);
  const remove = useDeleteSite();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);

  if (!site.data) return <ErrorText error={site.error} />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <Link to="/" className="text-xs text-ink-soft hover:text-ink">
            ← Sites
          </Link>
          <h1 className="text-xl font-semibold tracking-tight">{site.data.name}</h1>
          <a
            href={site.data.start_url}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-xs text-accent"
          >
            {site.data.start_url}
          </a>
        </div>
        <Button
          tone="primary"
          disabled={start.isPending}
          onClick={() =>
            start.mutate(undefined, { onSuccess: (run) => navigate(`/runs/${run.id}`) })
          }
        >
          Run analysis
        </Button>
      </div>
      <ErrorText error={start.error} />

      <Card title="Analyses">
        {runs.data?.length === 0 && <p className="text-sm text-ink-soft">No analyses yet.</p>}
        <ul className="-my-2 divide-y divide-line">
          {runs.data?.map((run) => (
            <li key={run.id}>
              <Link
                to={`/runs/${run.id}`}
                className="flex items-center justify-between py-2.5 text-sm hover:text-accent"
              >
                <span>{formatDate(run.created_at)}</span>
                <span className="flex items-center gap-3 text-ink-soft">
                  {typeof run.progress.pages === "number" && (
                    <span>{run.progress.pages} pages</span>
                  )}
                  <StatusBadge value={run.status} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </Card>

      <Card
        title="Settings"
        actions={!editing && <Button onClick={() => setEditing(true)}>Edit</Button>}
      >
        {editing ? (
          <>
            <ProfileForm
              name={site.data.name}
              initial={fromProfile(site.data.profile)}
              submitLabel="Save"
              busy={update.isPending}
              onSubmit={(name, values) =>
                update.mutate(
                  { name, profile: toProfile(values) },
                  { onSuccess: () => setEditing(false) },
                )
              }
            />
            <div className="mt-3">
              <ErrorText error={update.error} />
            </div>
          </>
        ) : (
          <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-4">
            <Summary label="Scope" value={site.data.profile.scope ?? "site"} />
            <Summary label="Viewports" value={(site.data.profile.viewports ?? []).join(", ")} />
            <Summary label="Language" value={(site.data.profile.language ?? "en").toUpperCase()} />
            <Summary
              label="Limits"
              value={`${site.data.profile.limits?.max_pages ?? 25} pages · depth ${site.data.profile.limits?.max_depth ?? 3}`}
            />
          </dl>
        )}
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Credentials siteId={siteId} configured={site.data.has_credentials} />
        <ExtensionKey siteId={siteId} configured={site.data.has_extension_key} />
      </div>

      <div className="flex justify-end">
        <Button
          tone="danger"
          onClick={() => {
            if (confirm(`Delete ${site.data.name} and all of its analyses?`)) {
              remove.mutate(siteId, { onSuccess: () => navigate("/") });
            }
          }}
        >
          Delete site
        </Button>
      </div>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-ink-faint">{label}</dt>
      <dd className="capitalize">{value}</dd>
    </div>
  );
}

function Credentials({ siteId, configured }: { siteId: string; configured: boolean }) {
  const { saveCredentials, clearCredentials } = useSiteSecrets(siteId);
  const blank = {
    login_url: "",
    username: "",
    password: "",
    username_selector: "",
    password_selector: "",
    submit_selector: "",
  };
  const [form, setForm] = useState(blank);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const optional = (value: string) => value.trim() || null;
    saveCredentials.mutate(
      {
        ...form,
        username_selector: optional(form.username_selector),
        password_selector: optional(form.password_selector),
        submit_selector: optional(form.submit_selector),
      },
      { onSuccess: () => setForm(blank) },
    );
  };

  return (
    <Card
      title="Login"
      actions={configured && <Button onClick={() => clearCredentials.mutate()}>Remove</Button>}
    >
      <p className="mb-4 text-sm text-ink-soft">
        {configured
          ? "A login is stored, encrypted. Saving again replaces it."
          : "Optional. Lets the auditor reach pages behind a sign-in."}
      </p>
      <form onSubmit={submit} className="space-y-3">
        <Field label="Login page">
          <Input
            required
            value={form.login_url}
            onChange={(e) => setForm({ ...form, login_url: e.target.value })}
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Username">
            <Input
              required
              autoComplete="off"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </Field>
          <Field label="Password">
            <Input
              required
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
        </div>
        <details className="text-sm">
          <summary className="cursor-pointer text-ink-soft">
            Selectors (only if the form is unusual)
          </summary>
          <div className="mt-3 grid gap-3">
            {(["username_selector", "password_selector", "submit_selector"] as const).map(
              (name) => (
                <Field key={name} label={name.replace("_", " ")}>
                  <Input
                    value={form[name]}
                    placeholder="#email"
                    onChange={(e) => setForm({ ...form, [name]: e.target.value })}
                  />
                </Field>
              ),
            )}
          </div>
        </details>
        <ErrorText error={saveCredentials.error} />
        <Button type="submit" disabled={saveCredentials.isPending}>
          Save login
        </Button>
      </form>
    </Card>
  );
}

function ExtensionKey({ siteId, configured }: { siteId: string; configured: boolean }) {
  const { rotateKey, revokeKey } = useSiteSecrets(siteId);
  const key = rotateKey.data?.key;

  return (
    <Card
      title="Extension key"
      actions={configured && <Button onClick={() => revokeKey.mutate()}>Revoke</Button>}
    >
      <p className="mb-4 text-sm text-ink-soft">
        Enter this key in the Clarity Compass extension to open the site with the analysis overlay.{" "}
        <Link to="/extension" className="font-medium text-ink underline underline-offset-4">
          How to install the extension
        </Link>
      </p>
      {key ? (
        <div className="space-y-2">
          <CopyField value={key} />
          <p className="text-xs text-medium">Copy it now - it is not shown again.</p>
        </div>
      ) : (
        <Button onClick={() => rotateKey.mutate()} disabled={rotateKey.isPending}>
          {configured ? "Generate a new key" : "Generate key"}
        </Button>
      )}
    </Card>
  );
}
