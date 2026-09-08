import { createSlice } from '@reduxjs/toolkit';

export const appDownloadsSlice = createSlice({
	name: 'appDownloads',
	initialState: {
		exports: null,
	},
	reducers: {
		setAppDownloadsData: (state, action) => {
			state.exports = action.payload;
		},
	},
});

export const { setAppDownloadsData } = appDownloadsSlice.actions;

export const selectAppDownloadsData = (state) => state.appDownloads.exports;

export default appDownloadsSlice.reducer;
