import { createContext, useEffect, useMemo, useState } from 'react';

export const LoaderContext = createContext();

export default function LoaderContextProvider({ children, fullScreen = false }) {
	const [isLoading, setLoading] = useState(false);
	const [isVisible, setVisible] = useState(false);

	useEffect(() => {
		if (isLoading) {
			setVisible(isLoading);
		}
	}, [isLoading]);

	const contextValue = useMemo(() => {
		return { isVisible, setLoading, isLoading };
	}, [isVisible, isLoading]);

	return (
		<LoaderContext.Provider value={contextValue}>
			{children}
			{isLoading && <div className={fullScreen ? "overlay-spinner" : "page-loader"} />}
		</LoaderContext.Provider>
	);
}
