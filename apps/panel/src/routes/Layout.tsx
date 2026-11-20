import { Link, Navigate, Outlet, useLocation, useNavigate } from "react-router";
import { useLogout, useMe } from "@/api/hooks";
import { Logo } from "@/components/Logo";
import { Landing } from "./Landing";

export function Layout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  if (me.isPending) return null;
  if (me.isError) return pathname === "/" ? <Landing /> : <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-white/85 backdrop-blur print:hidden">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/">
            <Logo />
          </Link>
          <div className="flex items-center gap-5 text-sm text-ink-soft">
            <span className="hidden font-mono text-xs sm:inline">{me.data.username}</span>
            <button
              type="button"
              className="transition-colors hover:text-ink"
              onClick={() => logout.mutate(undefined, { onSuccess: () => navigate("/") })}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-10 print:max-w-none print:p-0">
        <Outlet />
      </main>
    </div>
  );
}
