import { useSimulation } from "@/api/hooks";
import { HeatImage } from "./HeatImage";
import { ErrorText } from "./ui";

interface FrameResult {
  screenshot: string;
  heat: string;
  attention: number;
  rank: number;
  elements: number;
}

interface Result {
  explanation: string;
  before: FrameResult;
  after: FrameResult;
  change: number;
}

const artifact = (key: string) => `/api/artifacts/${key}`;
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export function SimulationView({ id }: { id: string }) {
  const simulation = useSimulation(id);
  const data = simulation.data;
  if (!data) return <ErrorText error={simulation.error} />;
  if (data.status === "queued" || data.status === "running") {
    return <p className="text-sm text-ink-soft">Rendering the fix and measuring attention…</p>;
  }
  if (data.error) return <ErrorText error={data.error} />;
  const result = data.result as unknown as Result;

  return (
    <div className="space-y-3">
      <p className="text-sm">{result.explanation}</p>
      <p className="text-sm">
        Attention on the element: <strong>{percent(result.before.attention)}</strong> →{" "}
        <strong className="text-ink">{percent(result.after.attention)}</strong>{" "}
        <span className="text-ink-soft">
          (rank {result.before.rank} → {result.after.rank} of {result.after.elements})
        </span>
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {(["before", "after"] as const).map((side) => (
          <figure key={side} className="space-y-1">
            <figcaption className="text-xs font-medium capitalize text-ink-soft">{side}</figcaption>
            <HeatImage
              screenshot={artifact(result[side].screenshot)}
              attention={artifact(result[side].heat)}
              showHeat
              className="w-full [&_img]:h-auto [&_img]:w-full"
            />
          </figure>
        ))}
      </div>
    </div>
  );
}
