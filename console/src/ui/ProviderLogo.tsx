import type { ReactNode } from 'react';
import { cx } from './cx';

// Logos and copy for the AI services Zango can connect to (inline SVG, no network).
// The marks are the ones the classic App Panel uses.

export interface ServiceMeta {
	name: string;
	/** One line under the name in pickers. */
	tagline: string;
	/** Tile background behind the mark. */
	tile: string;
	/** Where to get a key, shown next to the credential fields. */
	keyHelp?: { label: string; href: string };
}

export const SERVICES: Record<string, ServiceMeta> = {
	anthropic: {
		name: 'Anthropic',
		tagline: 'Claude Opus, Sonnet and Haiku',
		tile: '#F3EEE7',
		keyHelp: { label: 'Anthropic Console → API keys', href: 'https://console.anthropic.com/settings/keys' },
	},
	claude_subscription: {
		name: 'Claude subscription',
		tagline: 'Your Claude login, for local testing only',
		tile: '#F3EEE7',
	},
	openai: {
		name: 'OpenAI',
		tagline: 'GPT and o-series models',
		tile: '#F4F4F5',
		keyHelp: { label: 'OpenAI Platform → API keys', href: 'https://platform.openai.com/api-keys' },
	},
	azure_openai: {
		name: 'Azure OpenAI',
		tagline: 'OpenAI models in your Azure tenant',
		tile: '#EAF3FC',
		keyHelp: { label: 'Azure portal → your OpenAI resource → Keys and Endpoint', href: 'https://portal.azure.com' },
	},
	bedrock: {
		name: 'AWS Bedrock',
		tagline: 'Claude, Llama and more in your AWS account',
		tile: '#232F3E',
		keyHelp: { label: 'AWS console → IAM → access keys', href: 'https://console.aws.amazon.com/iam' },
	},
};

export const serviceMeta = (slug: string | null | undefined): ServiceMeta =>
	(slug && SERVICES[slug]) || {
		name: slug || 'AI service',
		tagline: '',
		tile: 'var(--subtle)',
	};

function Anthropic() {
	return (
		<svg viewBox="0 0 46 32" fill="none" aria-hidden>
			<path d="M32.73 0h-6.945L38.74 32h6.945L32.73 0Z" fill="#181818" />
			<path
				d="M13.055 0 0.315 32h7.109l2.656-6.8h13.6l2.656 6.8h7.11L18.705 0h-5.65Zm-.78 19.367 4.44-11.371 4.44 11.371h-8.88Z"
				fill="#181818"
			/>
		</svg>
	);
}

function OpenAI() {
	return (
		<svg viewBox="0 0 32 32" fill="none" aria-hidden>
			<path
				d="M29.71 13.09A8.09 8.09 0 0 0 20.78 4a8.1 8.1 0 0 0-13.7 3A8.1 8.1 0 0 0 2.29 18.9 8.1 8.1 0 0 0 11.22 28a8.09 8.09 0 0 0 13.69-3A8.1 8.1 0 0 0 29.71 13.09Zm-12.4 17.3a6 6 0 0 1-3.84-1.39l.19-.11 6.37-3.68a1 1 0 0 0 .53-.92v-8.98l2.69 1.56a.09.09 0 0 1 .05.07v7.44a6 6 0 0 1-6 6.01Zm-12.89-5.5a6 6 0 0 1-.72-4 5.89 5.89 0 0 0 1 .17l6.37 3.68a1 1 0 0 0 1.06 0l7.78-4.49v3.12a.1.1 0 0 1-.04.08L13.48 27a6 6 0 0 1-8.06-2.11ZM3.29 10.52a6 6 0 0 1 3.13-2.64v7.58a1 1 0 0 0 .51.9l7.75 4.47-2.7 1.56a.1.1 0 0 1-.09 0L5.41 18.4a6 6 0 0 1-2.12-7.88Zm22.13 5.15-7.78-4.52 2.7-1.55a.1.1 0 0 1 .09 0l6.48 3.74a6 6 0 0 1-.93 10.82v-7.58a1.06 1.06 0 0 0-.56-.91Zm2.68-4.06a5.9 5.9 0 0 0-1-.17l-6.37-3.68a1 1 0 0 0-1.06 0L11.9 12.25V9.13a.09.09 0 0 1 .04-.08L18.43 5a6 6 0 0 1 9 6.61ZM10.55 17.1l-2.69-1.55a.09.09 0 0 1-.05-.07V8.03a6 6 0 0 1 9.84-4.6l-.19.11-6.37 3.68a1 1 0 0 0-.53.91l-.01 8.97Zm1.46-3.15 3.46-2 3.46 2v4l-3.46 2-3.46-2v-4Z"
				fill="#181818"
			/>
		</svg>
	);
}

function Azure() {
	return (
		<svg viewBox="0 0 96 96" aria-hidden>
			<defs>
				<linearGradient id="zpl-az1" x1="58.97" y1="9.06" x2="31.98" y2="88.79" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopColor="#114a8b" />
					<stop offset="1" stopColor="#0669bc" />
				</linearGradient>
				<linearGradient id="zpl-az3" x1="46.1" y1="6.54" x2="75.55" y2="87.2" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopColor="#3ccbf4" />
					<stop offset="1" stopColor="#2892df" />
				</linearGradient>
			</defs>
			<path
				d="M33.338 6.544h26.038l-27.03 80.087a4.152 4.152 0 0 1-3.933 2.824H8.149a4.145 4.145 0 0 1-3.928-5.47L29.405 9.368a4.152 4.152 0 0 1 3.933-2.824z"
				fill="url(#zpl-az1)"
			/>
			<path
				d="M71.175 60.261h-41.29L53.44 6.544H29.395A4.15 4.15 0 0 0 25.47 9.37L.222 83.985a4.145 4.145 0 0 0 3.928 5.47h20.343a4.15 4.15 0 0 0 3.896-2.693z"
				fill="#0078d4"
			/>
			<path
				d="M66.595 9.368A4.145 4.145 0 0 0 62.67 6.54H33.648a4.145 4.145 0 0 1 3.925 2.828l25.184 74.616a4.145 4.145 0 0 1-3.925 5.472h29.02a4.145 4.145 0 0 0 3.924-5.472z"
				fill="url(#zpl-az3)"
			/>
		</svg>
	);
}

function Aws() {
	return (
		<svg viewBox="0 0 40 26" fill="none" aria-hidden>
			<text
				x="20"
				y="14"
				textAnchor="middle"
				fill="#fff"
				fontSize="13"
				fontWeight="700"
				fontFamily="Arial, Helvetica, sans-serif"
				letterSpacing="-0.3"
			>
				aws
			</text>
			<path d="M8 18.5c7 4 17 4 24 0" stroke="#FF9900" strokeWidth="2" strokeLinecap="round" />
			<path d="M29.5 16.6l3 1.6-1.3 3" stroke="#FF9900" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
		</svg>
	);
}

const MARKS: Record<string, () => ReactNode> = {
	anthropic: Anthropic,
	claude_subscription: Anthropic,
	openai: OpenAI,
	azure_openai: Azure,
	bedrock: Aws,
};

/** A service's mark on its brand tile. */
export function ProviderLogo({
	slug,
	size = 36,
	className,
}: {
	slug: string | null | undefined;
	size?: number;
	className?: string;
}) {
	const meta = serviceMeta(slug);
	const Mark = slug ? MARKS[slug] : undefined;
	return (
		<span
			className={cx('zpl', className)}
			style={{ width: size, height: size, background: meta.tile, borderRadius: Math.round(size * 0.28) }}
			title={meta.name}
		>
			{Mark ? (
				<span className="zpl-m" style={{ width: size * 0.58, height: size * 0.58 }}>
					<Mark />
				</span>
			) : (
				<span className="zpl-t" style={{ fontSize: size * 0.4 }}>
					{meta.name.slice(0, 1).toUpperCase()}
				</span>
			)}
		</span>
	);
}
