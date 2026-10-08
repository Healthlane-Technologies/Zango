import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

// Django serves the bundle through the `use_latest` template filter, which picks
// the lexically greatest file name matching console.*.min.{js,css}. A timestamp
// keeps that ordering correct; content hashes would not.
const stamp = Date.now();
const DJANGO = process.env.ZANGO_DEV_SERVER ?? 'http://localhost:8000';

export default defineConfig(({ command }) => ({
	plugins: [react()],
	base: command === 'build' ? '/static/console/' : '/',
	resolve: {
		alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
	},
	server: {
		port: 5173,
		proxy: Object.fromEntries(
			['/api', '/auth', '/static', '/session_security'].map((p) => [p, { target: DJANGO }])
		),
	},
	build: {
		outDir: '../backend/src/zango/assets/console',
		emptyOutDir: true,
		sourcemap: false,
		// One stylesheet (about 78 kB): the template links a single console.<stamp>.min.css,
		// and split CSS chunks would need names outside that pattern.
		cssCodeSplit: false,
		rollupOptions: {
			input: 'src/main.tsx',
			output: {
				entryFileNames: `console.${stamp}.min.js`,
				chunkFileNames: `chunks/[name].[hash].js`,
				assetFileNames: (asset) =>
					asset.names?.some((n) => n.endsWith('.css'))
						? `console.${stamp}.min.css`
						: 'assets/[name].[hash][extname]',
			},
		},
	},
}));
