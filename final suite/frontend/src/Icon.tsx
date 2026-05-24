import { SVGProps } from "react";

type IconName =
  | "flame"
  | "map"
  | "chart"
  | "target"
  | "swap"
  | "star"
  | "check"
  | "rocket"
  | "spinner"
  | "play"
  | "pause"
  | "skipBack"
  | "skipForward"
  | "rewind"
  | "fastForward"
  | "caretRight"
  | "menu"
  | "close";

interface Props extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName;
  size?: number | string;
}

const PATHS: Record<IconName, JSX.Element> = {
  // Sleek flame outline (Phosphor-style)
  flame: (
    <>
      <path d="M12 2.5c1.6 3.2 4.6 4.9 4.6 8.5a4.6 4.6 0 0 1-9.2 0c0-1.7.8-2.9 1.7-3.6.4 1 1.1 1.6 1.9 1.6 0-2.4.2-4.4 1-6.5z" />
      <path d="M12 21.5a5.5 5.5 0 0 0 5.5-5.5c0-3-2.2-4.5-3.4-6.8" opacity=".55" />
    </>
  ),
  map: (
    <>
      <path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z" />
      <path d="M9 4v14M15 6v14" />
    </>
  ),
  chart: (
    <>
      <path d="M4 21V5M4 21h16" />
      <rect x="7.5" y="12" width="3" height="6" rx="0.5" />
      <rect x="12.5" y="8" width="3" height="10" rx="0.5" />
      <rect x="17.5" y="14" width="3" height="4" rx="0.5" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5.5" />
      <circle cx="12" cy="12" r="2" fill="currentColor" stroke="none" />
    </>
  ),
  swap: (
    <>
      <path d="M4 8h13l-3-3" />
      <path d="M20 16H7l3 3" />
    </>
  ),
  star: (
    <path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1.1 5.9L12 16.9l-5.3 2.8 1.1-5.9L3.5 9.7l5.9-.8L12 3.5z" />
  ),
  check: <path d="M4.5 12.5l4.5 4.5L19.5 6.5" />,
  rocket: (
    <>
      <path d="M13.5 3.5c4 0 7 3 7 7-2 2-4 3-5.5 3l-4.5-4.5c0-1.5 1-3.5 3-5.5z" />
      <path d="M10.5 9 5 14.5l4.5 4.5L15 13.5" />
      <path d="M7 17l-3 3" />
      <circle cx="15" cy="9" r="1.2" fill="currentColor" stroke="none" />
    </>
  ),
  spinner: (
    <>
      <circle cx="12" cy="12" r="9" opacity=".22" />
      <path d="M21 12a9 9 0 0 0-9-9" />
    </>
  ),
  play: <path d="M7 4.5v15l13-7.5z" />,
  pause: (
    <>
      <rect x="6.5" y="4.5" width="4" height="15" rx="1" />
      <rect x="13.5" y="4.5" width="4" height="15" rx="1" />
    </>
  ),
  skipBack: (
    <>
      <path d="M19 5v14l-11-7z" />
      <rect x="4" y="5" width="2.5" height="14" rx="0.5" />
    </>
  ),
  skipForward: (
    <>
      <path d="M5 5v14l11-7z" />
      <rect x="17.5" y="5" width="2.5" height="14" rx="0.5" />
    </>
  ),
  rewind: (
    <>
      <path d="M12 5v14L2 12z" />
      <path d="M22 5v14L12 12z" />
    </>
  ),
  fastForward: (
    <>
      <path d="M2 5v14l10-7z" />
      <path d="M12 5v14l10-7z" />
    </>
  ),
  caretRight: <path d="M9 5l7 7-7 7z" fill="currentColor" stroke="none" />,
  menu: (
    <>
      <path d="M4 6h16" />
      <path d="M4 12h16" />
      <path d="M4 18h16" />
    </>
  ),
  close: (
    <>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </>
  ),
};

const FILLED: Set<IconName> = new Set(["play", "pause", "skipBack", "skipForward", "rewind", "fastForward", "star"]);

export default function Icon({ name, size = "1em", ...rest }: Props) {
  const filled = FILLED.has(name);
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  );
}
