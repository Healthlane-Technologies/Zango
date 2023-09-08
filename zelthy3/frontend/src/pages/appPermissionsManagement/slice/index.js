import { createSlice } from '@reduxjs/toolkit';

export const appPermissionsManagementSlice = createSlice({
	name: 'appPermissionsManagement',
	initialState: {
		isAddCustomPermissionModalOpen: false,
		isEditCustomPermissionModalOpen: false,
		isDeleteCustomPermissionModalOpen: false,
		rerenderPage: false,
		appPermissionsManagementData: null,
		appPermissionsManagementFormData: null,
	},
	reducers: {
		toggleIsAddCustomPermissionModalOpen: (state) => {
			state.isAddCustomPermissionModalOpen +=
				!state.isAddCustomPermissionModalOpen;
		},
		openIsAddCustomPermissionModalOpen: (state, action) => {
			state.isAddCustomPermissionModalOpen = true;
			state.appPermissionsManagementFormData = action.payload;
		},
		closeIsAddCustomPermissionModalOpen: (state) => {
			state.isAddCustomPermissionModalOpen = false;
			state.appPermissionsManagementFormData = null;
		},
		toggleIsEditCustomPermissionModalOpen: (state) => {
			state.isEditCustomPermissionModalOpen +=
				!state.isEditCustomPermissionModalOpen;
		},
		openIsEditCustomPermissionModalOpen: (state, action) => {
			state.isEditCustomPermissionModalOpen = true;
			state.appPermissionsManagementFormData = action.payload;
		},
		closeIsEditCustomPermissionModalOpen: (state) => {
			state.isEditCustomPermissionModalOpen = false;
			state.appPermissionsManagementFormData = null;
		},
		toggleIsDeleteCustomPermissionModalOpen: (state) => {
			state.isDeleteCustomPermissionModalOpen +=
				!state.isDeleteCustomPermissionModalOpen;
		},
		openIsDeleteCustomPermissionModalOpen: (state, action) => {
			state.isDeleteCustomPermissionModalOpen = true;
			state.appPermissionsManagementFormData = action.payload;
		},
		closeIsDeleteCustomPermissionModalOpen: (state) => {
			state.isDeleteCustomPermissionModalOpen = false;
			state.appPermissionsManagementFormData = null;
		},
		setAppPermissionsManagementData: (state, action) => {
			state.appPermissionsManagementData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsAddCustomPermissionModalOpen,
	openIsAddCustomPermissionModalOpen,
	closeIsAddCustomPermissionModalOpen,
	toggleIsEditCustomPermissionModalOpen,
	openIsEditCustomPermissionModalOpen,
	closeIsEditCustomPermissionModalOpen,
	toggleIsDeleteCustomPermissionModalOpen,
	openIsDeleteCustomPermissionModalOpen,
	closeIsDeleteCustomPermissionModalOpen,
	setAppPermissionsManagementData,
	toggleRerenderPage,
} = appPermissionsManagementSlice.actions;

export const selectIsAddCustomPermissionModalOpen = (state) =>
	state.appPermissionsManagement.isAddCustomPermissionModalOpen;

export const selectIsEditCustomPermissionModalOpen = (state) =>
	state.appPermissionsManagement.isEditCustomPermissionModalOpen;

export const selectIsDeleteCustomPermissionModalOpen = (state) =>
	state.appPermissionsManagement.isDeleteCustomPermissionModalOpen;

export const selectRerenderPage = (state) =>
	state.appPermissionsManagement.rerenderPage;

export const selectAppPermissionsManagementData = (state) =>
	state.appPermissionsManagement.appPermissionsManagementData;

export const selectAppPermissionsManagementFormData = (state) =>
	state.appPermissionsManagement.appPermissionsManagementFormData;

export default appPermissionsManagementSlice.reducer;
