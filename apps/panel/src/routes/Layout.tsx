import { Link, Navigate, Outlet, useNavigate } from "react-router";
import { useLogout, useMe } from "@/api/hooks";

export function Layout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();

  if (me.isPending) return null;
  if (me.isError) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="grid size-6 place-items-center rounded-full border-2 border-accent">
              <span className="size-1.5 rounded-full bg-accent" />
            </span>
            Clarity Compass
          </Link>
          <div className="flex items-center gap-4 text-sm text-ink-soft">
            <span>{me.data.username}</span>
            <button
              type="button"
              className="hover:text-ink"
              onClick={() => logout.mutate(undefined, { onSuccess: () => navigate("/login") })}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
