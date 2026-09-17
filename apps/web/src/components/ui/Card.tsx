import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={
        "rounded-2xl border border-line bg-surface/90 p-8 shadow-xl shadow-black/5 backdrop-blur-sm " +
        className
      }
    >
      {children}
    </div>
  );
}
