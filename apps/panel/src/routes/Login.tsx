import { type FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router";
import { useLogin, useMe } from "@/api/hooks";
import { Button, ErrorText, Field, Input } from "@/components/ui";

export function Login() {
  const me = useMe();
  const login = useLogin();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");

  if (me.isSuccess) return <Navigate to="/" replace />;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    login.mutate({ username, password }, { onSuccess: () => navigate("/") });
  };

  return (
    <div className="grid min-h-screen place-items-center px-6">
      <form
        onSubmit={submit}
        className="w-full max-w-sm space-y-5 rounded-lg border border-line bg-white p-8"
      >
        <div>
          <h1 className="text-lg font-semibold">Clarity Compass</h1>
          <p className="text-sm text-ink-soft">Sign in to continue.</p>
        </div>
        <Field label="Username">
          <Input
            autoComplete="username"
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
          className="w-full justify-center"
          disabled={login.isPending}
        >
          Sign in
        </Button>
      </form>
    </div>
  );
}
