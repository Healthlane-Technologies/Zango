import type { Config } from 'tailwindcss';

const v = (name: string) => `var(--${name})`;
const tone = (name: string) => ({ DEFAULT: v(name), soft: v(`${name}-soft`), t: v(`${name}-t`) });

export default {
	content: ['./index.html', './src/**/*.{ts,tsx}'],
	theme: {
		extend: {
			fontFamily: { sans: v('font'), mono: v('mono') },
			colors: {
				bg: v('bg'),
				panel: v('panel'),
				subtle: v('subtle'),
				hover: v('hover'),
				border: { DEFAULT: v('border'), 2: v('border-2'), soft: v('border-soft') },
				t1: v('t1'),
				t2: v('t2'),
				t3: v('t3'),
				t4: v('t4'),
				accent: { DEFAULT: v('accent'), h: v('accent-h'), soft: v('accent-soft'), t: v('accent-t') },
				navy: v('navy'),
				green: tone('green'),
				amber: tone('amber'),
				red: tone('red'),
				violet: tone('violet'),
				teal: tone('teal'),
			},
			boxShadow: { pop: v('sh-pop'), card: v('sh-card') },
			ringColor: { DEFAULT: v('ring') },
			transitionTimingFunction: { out: v('ease') },
		},
	},
	plugins: [],
} satisfies Config;
