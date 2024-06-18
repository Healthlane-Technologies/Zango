import React from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import './App.css';
import ErrorMessageContextProvider from './context/ErrorMessageContextProvider';
import LoaderContextProvider from './context/LoaderContextProvider';
import { AppRoutes } from './routes';
import store from './store';

function App() {
	return (
		<ErrorMessageContextProvider>
			<LoaderContextProvider>
				<Provider store={store}>
					<BrowserRouter basename="/">
						<AppRoutes />
					</BrowserRouter>
				</Provider>
			</LoaderContextProvider>
		</ErrorMessageContextProvider>
	);
}

export default App;
