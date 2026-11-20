import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { useCreateSite, useSites } from "@/api/hooks";
import { ProfileForm } from "@/components/ProfileForm";
import { toProfile } from "@/components/profile";
import { Button, Card, ErrorText } from "@/components/ui";

export function Sites() {
  const sites = useSites();
  const create = useCreateSite();
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Sites</h1>
          <p className="text-sm text-ink-soft">Websites you audit and their analysis settings.</p>
        </div>
        {!adding && (
          <Button tone="primary" onClick={() => setAdding(true)}>
            Add site
          </Button>
        )}
      </div>

      {adding && (
        <Card title="New site" actions={<Button onClick={() => setAdding(false)}>Cancel</Button>}>
          <ProfileForm
            submitLabel="Create site"
            busy={create.isPending}
            onSubmit={(name, values) =>
              create.mutate(
                { name, profile: toProfile(values) },
                { onSuccess: (site) => navigate(`/sites/${site.id}`) },
              )
            }
          />
          <div className="mt-3">
            <ErrorText error={create.error} />
          </div>
        </Card>
      )}

      <div className="overflow-hidden rounded-lg border border-line bg-white">
        {sites.data?.length === 0 && (
          <p className="p-8 text-center text-sm text-ink-soft">
            No sites yet. Add the first one to start an audit.
          </p>
        )}
        <ul className="divide-y divide-line">
          {sites.data?.map((site) => (
            <li key={site.id}>
              <Link
                to={`/sites/${site.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-paper"
              >
                <div>
                  <p className="font-medium">{site.name}</p>
                  <p className="font-mono text-xs text-ink-soft">{site.start_url}</p>
                </div>
                <span className="text-xs text-ink-faint capitalize">
                  {site.profile.scope} scope
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
