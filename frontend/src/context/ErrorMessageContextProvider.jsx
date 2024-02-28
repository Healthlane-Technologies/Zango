import { createContext, useEffect, useState } from 'react';
import ErrorMessageModal from '../components/ErrorMessageModal';

export const ErrorMessageContext = createContext({});

export default function ErrorMessageContextProvider({ children }) {
	const [errorMessage, setErrorMessage] = useState('');
	const [isVisible, setVisible] = useState(false);

	useEffect(() => {
		if (errorMessage) {
			setVisible(true);
		}
	}, [errorMessage]);

	useEffect(() => {
		if (!isVisible) {
			setErrorMessage('');
		}
	}, [isVisible]);

	return (
		<ErrorMessageContext.Provider value={setErrorMessage}>
			{children}
			<ErrorMessageModal
				isVisible={isVisible}
				setVisible={setVisible}
				errorMessage={errorMessage}
			/>
		</ErrorMessageContext.Provider>
	);
}
