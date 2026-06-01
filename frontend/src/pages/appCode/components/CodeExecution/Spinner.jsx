import React from 'react';

/** Small inline spinner. Sized to sit in a 16/20/24px button or label. */
export default function Spinner({ size = 14, color = 'currentColor', className = '' }) {
	return (
		<span
			className={`inline-block align-[-0.15em] ${className}`}
			style={{ width: size, height: size }}
			aria-hidden="true"
		>
			<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
				<circle cx="12" cy="12" r="9" stroke={color} strokeOpacity="0.2" strokeWidth="3" />
				<path
					d="M21 12a9 9 0 0 1-9 9"
					stroke={color}
					strokeWidth="3"
					strokeLinecap="round"
				>
					<animateTransform
						attributeName="transform"
						type="rotate"
						from="0 12 12"
						to="360 12 12"
						dur="0.7s"
						repeatCount="indefinite"
					/>
				</path>
			</svg>
		</span>
	);
}
