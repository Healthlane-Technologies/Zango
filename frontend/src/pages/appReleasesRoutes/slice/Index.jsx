import { createSlice } from '@reduxjs/toolkit';

export const appReleasesSlice = createSlice({
	name: 'appReleases',
	initialState: {
		rerenderPage: false,
		appReleasesData: null,
        appReleasesFormData: null,
        appReleasesTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppReleasesDataEmpty: true,
	},
	reducers: {
		setAppReleasesData: (state, action) => {
			state.appReleasesData = action.payload;
			state.isAppReleasesDataEmpty =
				action.payload?.releases?.records?.length ||
				state?.appReleasesTableData?.searchValue ||
				state?.appReleasesTableData?.columns?.length
					? false
					: true;
		},
		setAppReleasesTableData: (state, action) => {
			state.appReleasesTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	setAppReleasesData,
	setAppReleasesTableData,
	toggleRerenderPage,
} = appReleasesSlice.actions;


export const selectIsDeactivateUserRolesModalOpen = (state) =>
	state.appReleases.isDeactivateUserRolesModalOpen;

export const selectRerenderPage = (state) => state.appAccessLogs.rerenderPage;

export const selectAppReleasesData = (state) =>
	state.appReleases.appReleasesData;

export const selectappReleasesFormData= (state) =>
	state.appReleases.appReleasesFormData;

export const selectAppReleasesTableData = (state) =>
	state.appReleases.appReleasesTableData;

export const selectIsAppReleasesDataEmpty = (state) =>
	state.appReleases.isAppReleasesDataEmpty;

export default appReleasesSlice.reducer;
