import { useEffect, useRef } from "react";
import { colorizeInPlace } from "./heat";

interface Props {
  screenshot: string;
  attention?: string | undefined;
  showHeat: boolean;
  className?: string;
}

export function HeatImage({ screenshot, attention, showHeat, className = "" }: Props) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const target = canvas.current;
    if (!target || !attention || !showHeat) return;
    let cancelled = false;
    const image = new Image();
    image.onload = () => {
      if (cancelled) return;
      target.width = image.naturalWidth;
      target.height = image.naturalHeight;
      const context = target.getContext("2d");
      if (!context) return;
      context.drawImage(image, 0, 0);
      const frame = context.getImageData(0, 0, target.width, target.height);
      colorizeInPlace(frame.data);
      context.putImageData(frame, 0, 0);
    };
    image.src = attention;
    return () => {
      cancelled = true;
    };
  }, [attention, showHeat]);

  return (
    <div className={`relative ${className}`}>
      <img
        src={screenshot}
        alt=""
        loading="lazy"
        className="h-full w-auto rounded border border-line"
      />
      {attention && showHeat && (
        <canvas
          ref={canvas}
          className="pointer-events-none absolute inset-0 h-full w-full rounded"
        />
      )}
    </div>
  );
}
