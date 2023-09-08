import { createSlice } from '@reduxjs/toolkit';

export const appUserManagementSlice = createSlice({
	name: 'appUserManagement',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
		rerenderPage: false,
		appUserManagementData: null,
		appUserManagementFormData: null,
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
		setAppUserManagementData: (state, action) => {
			state.appUserManagementData = action.payload;
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
	setAppUserManagementData,
	toggleRerenderPage,
} = appUserManagementSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.appUserManagement.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.appUserManagement.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.appUserManagement.isDeactivateUserModalOpen;

export const selectRerenderPage = (state) =>
	state.appUserManagement.rerenderPage;

export const selectAppUserManagementData = (state) =>
	state.appUserManagement.appUserManagementData;

export const selectAppUserManagementFormData = (state) =>
	state.appUserManagement.appUserManagementFormData;

export default appUserManagementSlice.reducer;
