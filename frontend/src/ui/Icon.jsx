const ICON_PATHS = {
  mic: (
    <g>
      <rect x="9" y="3" width="6" height="13" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3M8.5 21h7" />
    </g>
  ),
  micFilled: (stroke) => (
    <g>
      <rect x="9" y="3" width="6" height="13" rx="3" fill={stroke} stroke="none" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3M8.5 21h7" />
    </g>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  arrowRight: <path d="M5 12h14M13 6l6 6-6 6" />,
  arrowLeft: <path d="M19 12H5M11 6l-6 6 6 6" />,
  sparkle: (
    <path d="M12 3l1.6 4.6L18 9l-4.4 1.4L12 15l-1.6-4.6L6 9l4.4-1.4L12 3zM19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14z" />
  ),
  check: <path d="M5 12l4.5 4.5L19 7" strokeWidth="2.4" />,
  chevron: <path d="M9 6l6 6-6 6" />,
  close: <path d="M6 6l12 12M18 6L6 18" />,
  home: <path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-4v-7h-6v7H5a1 1 0 0 1-1-1v-9z" />,
  chat: <path d="M4 5h16v11H8l-4 4V5z" />,
  chart: <path d="M4 20V8M10 20v-7M16 20V4M22 20H2" />,
  user: (
    <g>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 4-7 8-7s8 3 8 7" />
    </g>
  ),
  waveform: <path d="M3 12h2M7 8v8M11 4v16M15 8v8M19 11v2" strokeLinecap="round" />,
  bolt: <path d="M13 3L4 14h6l-1 7 9-11h-6l1-7z" />,
  coin: (
    <g>
      <circle cx="12" cy="12" r="9" />
      <path d="M9 9c0-1.5 1.5-2 3-2s3 .8 3 2.2c0 2.8-6 1.7-6 4.6 0 1.4 1.5 2.2 3 2.2s3-.5 3-2M12 6v1.5M12 16.5V18" />
    </g>
  ),
  bag: <path d="M5 8h14l-1 13H6L5 8zM9 8V6a3 3 0 0 1 6 0v2" />,
  clock: (
    <g>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" strokeLinecap="round" />
    </g>
  ),
  upload: <path d="M12 16V4M6 10l6-6 6 6M4 20h16" />,
  keyboard: (
    <g>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <path d="M7 10h.01M11 10h.01M15 10h.01M17 10h.01M7 14h10" strokeLinecap="round" />
    </g>
  ),
  edit: <path d="M4 20l4-1L19 8l-3-3L5 16l-1 4zM14 6l3 3" />,
  trash: <path d="M5 7h14M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />,
  history: (
    <g>
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5" />
      <path d="M12 7v5l3 2" strokeLinecap="round" />
    </g>
  ),
  flame: <path d="M12 3c1 4-3 5-3 9a3 3 0 0 0 6 0c0-1.5-1-2.5-1-4 2 1 4 3 4 6a6 6 0 1 1-12 0c0-5 6-6 6-11z" />,
};

export default function Icon({ name, size = 22, stroke = 'currentColor', strokeWidth = 1.8, fill = 'none' }) {
  const path = ICON_PATHS[name];
  const content = typeof path === 'function' ? path(stroke) : path;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill}
      stroke={stroke}
      strokeWidth={strokeWidth}
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {content || null}
    </svg>
  );
}
