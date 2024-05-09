import { useLayoutEffect } from 'react';

function debounce(func, timeout = 0) {
	let timer;
	return (...args) => {
		clearTimeout(timer);
		timer = setTimeout(() => {
			func.apply(this, args);
		}, timeout);
	};
}

function updateSize() {
	let vh = window.innerHeight * 0.01;
	document.documentElement.style.setProperty('--vh', `${vh}px`);
	document.documentElement.style.setProperty(
		'--app-height',
		`${window.innerHeight}px`
	);
}

const heightChange = debounce(() => updateSize());

export function useWindowSizeHeight() {
	useLayoutEffect(() => {
		window.addEventListener('resize', heightChange);
		heightChange();
		return () => window.removeEventListener('resize', heightChange);
	}, []);
}
