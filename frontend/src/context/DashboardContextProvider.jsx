import React, { createContext, useContext, useReducer } from 'react';

const initialDashboardState = {
	isTrue: false,
};

const DashboardContext = createContext({ ...initialDashboardState });

const DashboardDispatchContext = createContext(() => {});

function dashboardReducer(dashboard, action) {
	switch (action.type) {
		case 'SET_BOOLEAN': {
			return {
				...dashboard,
				isTrue: action.payload.isTrue,
			};
		}
	}
}

export function DashboardContextProvider({ children }) {
	const [dashboardState, dispatch] = useReducer(
		dashboardReducer,
		initialDashboardState
	);

	return (
		<DashboardContext.Provider value={dashboardState}>
			<DashboardDispatchContext.Provider value={dispatch}>
				{children}
			</DashboardDispatchContext.Provider>
		</DashboardContext.Provider>
	);
}

export function useDashboard() {
	return useContext(DashboardContext);
}

export function useDashboardDispatch() {
	return useContext(DashboardDispatchContext);
}
