import { useCallback, useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Icon, Toaster } from '@/ui';
import { Breadcrumbs } from './crumbs';
import { CommandPalette, useCommandPaletteHotkey } from './CommandPalette';
import { DOCS_URL } from './nav';
import { Sidebar } from './Sidebar';

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);

// The page scrolls inside `.content`, not the window, so reset it on navigation.
function useResetScrollOnNavigate() {
	const { pathname } = useLocation();
	useEffect(() => {
		document.getElementById('content')?.scrollTo(0, 0);
	}, [pathname]);
}

export function Shell() {
	useResetScrollOnNavigate();
	const [paletteOpen, setPaletteOpen] = useState(false);
	const toggle = useCallback(() => setPaletteOpen((o) => !o), []);
	useCommandPaletteHotkey(toggle);

	return (
		<div className="shell">
			<Sidebar />
			<div className="main">
				<header className="top">
					<Breadcrumbs />
					<div className="r">
						<button type="button" className="search" onClick={() => setPaletteOpen(true)}>
							<Icon name="search" />
							Search…
							<kbd>{isMac ? '⌘K' : 'Ctrl K'}</kbd>
						</button>
						<a
							className="ib"
							href={DOCS_URL}
							target="_blank"
							rel="noopener noreferrer"
							aria-label="Documentation"
						>
							<Icon name="book" />
						</a>
					</div>
				</header>
				<div className="content" id="content">
					<Outlet />
				</div>
			</div>
			<CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
			<Toaster />
		</div>
	);
}
