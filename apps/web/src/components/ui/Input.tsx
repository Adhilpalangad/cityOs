import { type InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, id, className = "", ...props }, ref) => {
    const inputId = id ?? props.name ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div>
        <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-ink-muted">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={
            "h-11 w-full rounded-lg border border-line bg-surface px-3.5 text-[15px] text-ink " +
            "placeholder:text-ink-faint outline-none transition-colors " +
            "focus:border-brand focus:ring-2 focus:ring-brand/25 " +
            className
          }
          {...props}
        />
        {hint && <p className="mt-1.5 text-xs text-ink-faint">{hint}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
