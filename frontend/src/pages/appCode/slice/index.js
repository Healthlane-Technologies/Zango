import { createSlice } from '@reduxjs/toolkit';

export const appCodeSlice = createSlice({
	name: 'appCode',
	initialState: {
		appCodebaseData: null,
		isLoading: false,
		error: null,
	},
	reducers: {
		setAppCodebaseData: (state, action) => {
			state.appCodebaseData = action.payload;
		},
		setIsLoading: (state, action) => {
			state.isLoading = action.payload;
		},
		setError: (state, action) => {
			state.error = action.payload;
		},
	},
});

export const { setAppCodebaseData, setIsLoading, setError } = appCodeSlice.actions;

export const selectAppCodebaseData = (state) => state.appCode.appCodebaseData;
export const selectIsLoading = (state) => state.appCode.isLoading;
export const selectError = (state) => state.appCode.error;

export default appCodeSlice.reducer;