export function LogoMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className} aria-hidden="true">
      <rect width="36" height="36" rx="10" className="fill-brand" />
      <path
        d="M11 24V15.5L14.5 13V24M14.5 24V17.5L18 15V24M18 24V12.5L21.5 10V24M21.5 24V18.5L25 16V24"
        stroke="var(--brand-ink)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M9 24H27" stroke="var(--brand-ink)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <LogoMark />
      <span className="text-lg font-semibold tracking-tight text-ink">CityOS</span>
    </div>
  );
}
