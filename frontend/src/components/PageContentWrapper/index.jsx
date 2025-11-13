import { useContext } from 'react';
import { LoaderContext } from '../../context/LoaderContextProvider';

export default function PageContentWrapper({ children }) {
	const { isLoading } = useContext(LoaderContext);

	// Hide content while loading
	if (isLoading) {
		return null;
	}

	return <>{children}</>;
}