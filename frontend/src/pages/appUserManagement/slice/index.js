import { createSlice } from '@reduxjs/toolkit';

export const appUserManagementSlice = createSlice({
	name: 'appUserManagement',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
		isActivateUserModalOpen: false,
		isResetPasswordModalOpen: false,
		rerenderPage: false,
		appUserManagementData: null,
		appUserManagementFormData: null,
		appUserManagementTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppUserManagementDataEmpty: true,
	},
	reducers: {
		toggleIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = !state.isAddNewUserModalOpen;
		},
		openIsAddNewUserModalOpen: (state, action) => {
			state.isAddNewUserModalOpen = true;
			state.appUserManagementFormData = action.payload;
		},
		closeIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = false;
			state.appUserManagementFormData = null;
		},
		toggleIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = !state.isEditUserDetailModalOpen;
		},
		openIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = true;
			state.appUserManagementFormData = action.payload;
		},
		closeIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = false;
			state.appUserManagementFormData = action.payload;
		},
		toggleIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = !state.isDeactivateUserModalOpen;
		},
		openIsDeactivateUserModalOpen: (state, action) => {
			state.isDeactivateUserModalOpen = true;
			state.appUserManagementFormData = action.payload;
		},
		closeIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = false;
			state.appUserManagementFormData = null;
		},
		toggleIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = !state.isActivateUserModalOpen;
		},
		openIsActivateUserModalOpen: (state, action) => {
			state.isActivateUserModalOpen = true;
			state.appUserManagementFormData = action.payload;
		},
		closeIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = false;
			state.appUserManagementFormData = null;
		},
		toggleIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = !state.isResetPasswordModalOpen;
		},
		openIsResetPasswordModalOpen: (state, action) => {
			state.isResetPasswordModalOpen = true;
			state.appUserManagementFormData = action.payload;
		},
		closeIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = false;
			state.appUserManagementFormData = null;
		},
		setAppUserManagementData: (state, action) => {
			state.appUserManagementData = action.payload;
			state.isAppUserManagementDataEmpty =
				action.payload?.users?.records?.length ||
				state?.appUserManagementTableData?.searchValue ||
				state?.appUserManagementTableData?.columns?.length
					? false
					: true;
		},
		setAppUserManagementTableData: (state, action) => {
			state.appUserManagementTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsAddNewUserModalOpen,
	openIsAddNewUserModalOpen,
	closeIsAddNewUserModalOpen,
	toggleIsEditUserDetailModalOpen,
	openIsEditUserDetailModalOpen,
	closeIsEditUserDetailModalOpen,
	toggleIsDeactivateUserModalOpen,
	openIsDeactivateUserModalOpen,
	closeIsDeactivateUserModalOpen,
	toggleIsActivateUserModalOpen,
	openIsActivateUserModalOpen,
	closeIsActivateUserModalOpen,
	toggleIsResetPasswordModalOpen,
	openIsResetPasswordModalOpen,
	closeIsResetPasswordModalOpen,
	setAppUserManagementData,
	setAppUserManagementTableData,
	toggleRerenderPage,
} = appUserManagementSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.appUserManagement.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.appUserManagement.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.appUserManagement.isDeactivateUserModalOpen;

export const selectIsActivateUserModalOpen = (state) =>
	state.appUserManagement.isActivateUserModalOpen;

export const selectIsResetPasswordModalOpen = (state) =>
	state.appUserManagement.isResetPasswordModalOpen;

export const selectRerenderPage = (state) =>
	state.appUserManagement.rerenderPage;

export const selectAppUserManagementData = (state) =>
	state.appUserManagement.appUserManagementData;

export const selectAppUserManagementTableData = (state) =>
	state.appUserManagement.appUserManagementTableData;

export const selectAppUserManagementFormData = (state) =>
	state.appUserManagement.appUserManagementFormData;

export const selectIsAppUserManagementDataEmpty = (state) =>
	state.appUserManagement.isAppUserManagementDataEmpty;

export default appUserManagementSlice.reducer;
