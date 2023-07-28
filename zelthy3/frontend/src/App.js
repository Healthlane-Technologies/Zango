import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { DashboardContextProvider } from './context/DashboardContextProvider';
import LoaderContextProvider from './context/LoaderContextProvider';
import ErrorMessageContextProvider from './context/ErrorMessageContextProvider';
import { AppRoutes } from './routes';
import './App.css';

function App() {
	return (
		<DashboardContextProvider>
			<ErrorMessageContextProvider>
				<LoaderContextProvider>
					<BrowserRouter basename="/">
						<AppRoutes />
					</BrowserRouter>
				</LoaderContextProvider>
			</ErrorMessageContextProvider>
		</DashboardContextProvider>
	);
}

export default App;
