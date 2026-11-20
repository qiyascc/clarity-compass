import { type FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router";
import { useLogin, useMe } from "@/api/hooks";
import { Logo } from "@/components/Logo";
import { Button, ErrorText, Field, Input } from "@/components/ui";

export function Login() {
  const me = useMe();
  const login = useLogin();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  if (me.isSuccess) return <Navigate to="/" replace />;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    login.mutate({ username, password }, { onSuccess: () => navigate("/") });
  };

  return (
    <div className="grid min-h-screen place-items-center bg-white px-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-6">
        <div className="space-y-6">
          <Logo />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
            <p className="mt-1 text-sm text-ink-soft">Admin access only.</p>
          </div>
        </div>
        <Field label="Username">
          <Input
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </Field>
        <Field label="Password">
          <Input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <ErrorText error={login.error} />
        <Button
          type="submit"
          tone="primary"
          className="h-10 w-full justify-center"
          disabled={login.isPending}
        >
          Sign in
        </Button>
      </form>
    </div>
  );
}
