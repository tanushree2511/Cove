/**
 * The Cove mark: a sheltered bay (crescent opening to the right) above a tide line, on a coral tile.
 * Same drawing as public/cove.svg, so the favicon and the in-app logo always match.
 */
export function CoveMark({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="Cove"
      className={className}
    >
      <defs>
        <linearGradient id="cove-mark-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f58a6f" />
          <stop offset="1" stopColor="#e4573f" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="18" fill="url(#cove-mark-grad)" />
      <path d="M43 15.5a19 19 0 1 0 0 33 14.5 14.5 0 1 1 0-33z" fill="#fbeedd" />
      <path
        d="M18 44.5c4.6-3.6 9.4-3.6 14 0s9.4 3.6 14 0"
        fill="none"
        stroke="#e4573f"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
