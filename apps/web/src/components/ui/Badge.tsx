type Tone = "brand" | "success" | "danger" | "neutral";

const tones: Record<Tone, string> = {
  brand: "bg-brand/12 text-brand-strong",
  success: "bg-success/12 text-success",
  danger: "bg-danger/12 text-danger",
  neutral: "bg-surface-muted text-ink-muted",
};

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: Tone }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function StatusDot({ online }: { online: boolean }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {online && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60" />
      )}
      <span
        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${online ? "bg-success" : "bg-danger"}`}
      />
    </span>
  );
}
