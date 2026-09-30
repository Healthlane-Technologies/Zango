import type { ReactNode, SVGProps } from 'react';

// Stroke icons from design/prototype.html (24px grid, currentColor).
const paths = {
	apps: (
		<>
			<rect x="3" y="3" width="7" height="7" rx="1.5" />
			<rect x="14" y="3" width="7" height="7" rx="1.5" />
			<rect x="3" y="14" width="7" height="7" rx="1.5" />
			<rect x="14" y="14" width="7" height="7" rx="1.5" />
		</>
	),
	tpl: (
		<>
			<path d="M4 5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v4H4zM4 13h7v7H5a1 1 0 0 1-1-1zM15 13h5v6a1 1 0 0 1-1 1h-4z" />
		</>
	),
	pkg: (
		<>
			<path d="M21 8 12 3 3 8v8l9 5 9-5z" />
			<path d="M3 8l9 5 9-5M12 13v8" />
		</>
	),
	act: (
		<>
			<path d="M3 12h4l3-8 4 16 3-8h4" />
		</>
	),
	users: (
		<>
			<circle cx="9" cy="8" r="3.5" />
			<path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6" />
		</>
	),
	key: (
		<>
			<circle cx="8" cy="15" r="4" />
			<path d="m11 12 9-9M17 6l3 3" />
		</>
	),
	home: (
		<>
			<path d="M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />
		</>
	),
	agent: (
		<>
			<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />
			<path d="M19 17l.7 1.8 1.8.7-1.8.7L19 22l-.7-1.8-1.8-.7 1.8-.7z" />
		</>
	),
	rocket: (
		<>
			<path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2M9 15l-3-3 5-7c2-2.5 5.5-3 9-3 0 3.5-.5 7-3 9l-7 5z" />
			<circle cx="15" cy="9" r="1.6" />
		</>
	),
	shield: (
		<>
			<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z" />
		</>
	),
	cog: (
		<>
			<circle cx="12" cy="12" r="3" />
			<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
		</>
	),
	back: (
		<>
			<path d="M15 6l-6 6 6 6" />
		</>
	),
	plus: (
		<>
			<path d="M12 5v14M5 12h14" />
		</>
	),
	check: (
		<>
			<path d="m5 12.5 4.5 4.5L19 7" />
		</>
	),
	x: (
		<>
			<path d="M6 6l12 12M18 6 6 18" />
		</>
	),
	dots: (
		<>
			<circle cx="5" cy="12" r="1.3" />
			<circle cx="12" cy="12" r="1.3" />
			<circle cx="19" cy="12" r="1.3" />
		</>
	),
	search: (
		<>
			<circle cx="11" cy="11" r="7" />
			<path d="m20 20-3.5-3.5" />
		</>
	),
	ext: (
		<>
			<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
		</>
	),
	copy: (
		<>
			<rect x="8" y="8" width="12" height="12" rx="2" />
			<path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
		</>
	),
	clip: (
		<>
			<path d="m20 11-8.5 8.5a5 5 0 0 1-7-7L13 4a3.3 3.3 0 0 1 4.7 4.7L9.2 17.2a1.7 1.7 0 0 1-2.4-2.4L14.5 7" />
		</>
	),
	up: (
		<>
			<path d="M12 19V5M6 11l6-6 6 6" />
		</>
	),
	lock: (
		<>
			<rect x="5" y="11" width="14" height="10" rx="2" />
			<path d="M8 11V7a4 4 0 0 1 8 0v4" />
		</>
	),
	alert: (
		<>
			<path d="M12 3 2 20h20z" />
			<path d="M12 10v4M12 17h.01" />
		</>
	),
	file: (
		<>
			<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z" />
			<path d="M14 3v5h5" />
		</>
	),
	book: (
		<>
			<path d="M4 4h6a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4zM20 4h-6a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h7z" />
		</>
	),
	blank: (
		<>
			<rect x="4" y="4" width="16" height="16" rx="3" strokeDasharray="3 3" />
		</>
	),
	bot: (
		<>
			<rect x="4" y="8" width="16" height="12" rx="3" />
			<path d="M12 4v4M9 13h.01M15 13h.01M9 17h6" />
			<circle cx="12" cy="3.5" r="1" />
		</>
	),
	pulse: (
		<>
			<path d="M3 12h4l3-8 4 16 3-8h4" />
		</>
	),
	logs: (
		<>
			<path d="M4 6h16M4 10h16M4 14h10M4 18h7" />
		</>
	),
	badge: (
		<>
			<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z" />
			<path d="m9 12 2 2 4-4" />
		</>
	),
	sort: (
		<>
			<path d="M7 4v16M3 16l4 4 4-4M17 20V4M13 8l4-4 4 4" />
		</>
	),
	eye: (
		<>
			<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
			<circle cx="12" cy="12" r="3" />
		</>
	),
	zap: (
		<>
			<path d="M13 3 4 14h7l-1 7 9-11h-7z" />
		</>
	),
} satisfies Record<string, ReactNode>;

export type IconName = keyof typeof paths;

interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
	name: IconName;
	size?: number;
	weight?: number;
}

export function Icon({ name, size = 15, weight = 1.8, className, ...rest }: IconProps) {
	return (
		<svg
			viewBox="0 0 24 24"
			width={size}
			height={size}
			fill="none"
			stroke="currentColor"
			strokeWidth={weight}
			strokeLinecap="round"
			strokeLinejoin="round"
			aria-hidden
			className={`shrink-0 ${className ?? ''}`}
			{...rest}
		>
			{paths[name]}
		</svg>
	);
}
