import { createSlice } from '@reduxjs/toolkit';

export const appUserRolesSlice = createSlice({
	name: 'appUserRoles',
	initialState: {
		isAddNewUserRolesModalOpen: false,
		isEditUserRolesDetailModalOpen: false,
		isDeactivateUserRolesModalOpen: false,
		isActivateUserRolesModalOpen: false,
		rerenderPage: false,
		appUserRolesData: null,
		appUserRolesFormData: null,
		appUserRolesTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppUserRolesDataEmpty: true,
	},
	reducers: {
		toggleIsAddNewUserRolesModalOpen: (state) => {
			state.isAddNewUserRolesModalOpen = !state.isAddNewUserRolesModalOpen;
		},
		openIsAddNewUserRolesModalOpen: (state, action) => {
			state.isAddNewUserRolesModalOpen = true;
			state.appUserRolesFormData = action.payload;
		},
		closeIsAddNewUserRolesModalOpen: (state, action) => {
			state.isAddNewUserRolesModalOpen = false;
			state.appUserRolesFormData = null;
		},
		toggleIsEditUserRolesDetailModalOpen: (state) => {
			state.isEditUserRolesDetailModalOpen =
				!state.isEditUserRolesDetailModalOpen;
		},
		openIsEditUserRolesDetailModalOpen: (state, action) => {
			state.isEditUserRolesDetailModalOpen = true;
			state.appUserRolesFormData = action.payload;
		},
		closeIsEditUserRolesDetailModalOpen: (state) => {
			state.isEditUserRolesDetailModalOpen = false;
			state.appUserRolesFormData = null;
		},
		toggleIsDeactivateUserRolesModalOpen: (state) => {
			state.isDeactivateUserRolesModalOpen =
				!state.isDeactivateUserRolesModalOpen;
		},
		openIsDeactivateUserRolesModalOpen: (state, action) => {
			state.isDeactivateUserRolesModalOpen = true;
			state.appUserRolesFormData = action.payload;
		},
		closeIsDeactivateUserRolesModalOpen: (state) => {
			state.isDeactivateUserRolesModalOpen = false;
			state.appUserRolesFormData = null;
		},
		toggleIsActivateUserRolesModalOpen: (state) => {
			state.isActivateUserRolesModalOpen = !state.isActivateUserRolesModalOpen;
		},
		openIsActivateUserRolesModalOpen: (state, action) => {
			state.isActivateUserRolesModalOpen = true;
			state.appUserRolesFormData = action.payload;
		},
		closeIsActivateUserRolesModalOpen: (state) => {
			state.isActivateUserRolesModalOpen = false;
			state.appUserRolesFormData = null;
		},
		setAppUserRolesData: (state, action) => {
			state.appUserRolesData = action.payload;
			state.isAppUserRolesDataEmpty =
				action.payload?.roles?.records?.length ||
				state?.appUserRolesTableData?.searchValue ||
				state?.appUserRolesTableData?.columns?.length
					? false
					: true;
		},
		setAppUserRolesTableData: (state, action) => {
			state.appUserRolesTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsAddNewUserRolesModalOpen,
	openIsAddNewUserRolesModalOpen,
	closeIsAddNewUserRolesModalOpen,
	toggleIsEditUserRolesDetailModalOpen,
	openIsEditUserRolesDetailModalOpen,
	closeIsEditUserRolesDetailModalOpen,
	toggleIsDeactivateUserRolesModalOpen,
	openIsDeactivateUserRolesModalOpen,
	closeIsDeactivateUserRolesModalOpen,
	toggleIsActivateUserRolesModalOpen,
	openIsActivateUserRolesModalOpen,
	closeIsActivateUserRolesModalOpen,
	setAppUserRolesData,
	setAppUserRolesTableData,
	toggleRerenderPage,
} = appUserRolesSlice.actions;

export const selectIsAddNewUserRolesModalOpen = (state) =>
	state.appUserRoles.isAddNewUserRolesModalOpen;

export const selectIsEditUserRolesDetailModalOpen = (state) =>
	state.appUserRoles.isEditUserRolesDetailModalOpen;

export const selectIsDeactivateUserRolesModalOpen = (state) =>
	state.appUserRoles.isDeactivateUserRolesModalOpen;

export const selectIsActivateUserRolesModalOpen = (state) =>
	state.appUserRoles.isActivateUserRolesModalOpen;

export const selectRerenderPage = (state) => state.appUserRoles.rerenderPage;

export const selectAppUserRolesData = (state) =>
	state.appUserRoles.appUserRolesData;

export const selectAppUserRolesFormData = (state) =>
	state.appUserRoles.appUserRolesFormData;

export const selectAppUserRolesTableData = (state) =>
	state.appUserRoles.appUserRolesTableData;

export const selectIsAppUserRolesDataEmpty = (state) =>
	state.appUserRoles.isAppUserRolesDataEmpty;

export default appUserRolesSlice.reducer;
