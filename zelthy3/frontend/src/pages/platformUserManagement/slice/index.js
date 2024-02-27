import { createSlice } from '@reduxjs/toolkit';

export const platformUserManagementSlice = createSlice({
	name: 'platformUserManagement',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
		isActivateUserModalOpen: false,
		isResetPasswordModalOpen: false,
		rerenderPage: false,
		platformUserManagementData: null,
		platformUserManagementFormData: null,
		platformUserManagementTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
	},
	reducers: {
		toggleIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = !state.isAddNewUserModalOpen;
		},
		openIsAddNewUserModalOpen: (state, action) => {
			state.isAddNewUserModalOpen = true;
			state.platformUserManagementFormData = action.payload;
		},
		closeIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = false;
			state.platformUserManagementFormData = null;
		},
		toggleIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = !state.isEditUserDetailModalOpen;
		},
		openIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = true;
			state.platformUserManagementFormData = action.payload;
		},
		closeIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = false;
			state.platformUserManagementFormData = null;
		},
		toggleIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen += !state.isDeactivateUserModalOpen;
		},
		openIsDeactivateUserModalOpen: (state, action) => {
			state.isDeactivateUserModalOpen = true;
			state.platformUserManagementFormData = action.payload;
		},
		closeIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = false;
			state.platformUserManagementFormData = null;
		},
		toggleIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = !state.isActivateUserModalOpen;
		},
		openIsActivateUserModalOpen: (state, action) => {
			state.isActivateUserModalOpen = true;
			state.platformUserManagementFormData = action.payload;
		},
		closeIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = false;
			state.platformUserManagementFormData = null;
		},
		toggleIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = !state.isResetPasswordModalOpen;
		},
		openIsResetPasswordModalOpen: (state, action) => {
			state.isResetPasswordModalOpen = true;
			state.platformUserManagementFormData = action.payload;
		},
		closeIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = false;
			state.platformUserManagementFormData = null;
		},
		setPlatformUserManagementData: (state, action) => {
			state.platformUserManagementData = action.payload;
		},
		setPlatformUserManagementTableData: (state, action) => {
			state.platformUserManagementTableData = action.payload;
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
	setPlatformUserManagementData,
	setPlatformUserManagementTableData,
	toggleRerenderPage,
} = platformUserManagementSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.platformUserManagement.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.platformUserManagement.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.platformUserManagement.isDeactivateUserModalOpen;

export const selectIsActivateUserModalOpen = (state) =>
	state.platformUserManagement.isActivateUserModalOpen;

export const selectIsResetPasswordModalOpen = (state) =>
	state.platformUserManagement.isResetPasswordModalOpen;

export const selectRerenderPage = (state) =>
	state.platformUserManagement.rerenderPage;

export const selectPlatformUserManagementData = (state) =>
	state.platformUserManagement.platformUserManagementData;

export const selectPlatformUserManagementTableData = (state) =>
	state.platformUserManagement.platformUserManagementTableData;

export const selectPlatformUserManagementFormData = (state) =>
	state.platformUserManagement.platformUserManagementFormData;

export default platformUserManagementSlice.reducer;
