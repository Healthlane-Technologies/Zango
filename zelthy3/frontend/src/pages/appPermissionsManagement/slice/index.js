import { createSlice } from '@reduxjs/toolkit';

export const appPermissionsManagementSlice = createSlice({
	name: 'appPermissionsManagement',
	initialState: {
		isAddCustomPermissionModalOpen: false,
		isEditCustomPermissionModalOpen: false,
		isDeleteCustomPermissionModalOpen: false,
	},
	reducers: {
		toggleIsAddCustomPermissionModalOpen: (state) => {
			state.isAddCustomPermissionModalOpen +=
				!state.isAddCustomPermissionModalOpen;
		},
		openIsAddCustomPermissionModalOpen: (state) => {
			state.isAddCustomPermissionModalOpen = true;
		},
		closeIsAddCustomPermissionModalOpen: (state, action) => {
			state.isAddCustomPermissionModalOpen = false;
		},
		toggleIsEditCustomPermissionModalOpen: (state) => {
			state.isEditCustomPermissionModalOpen +=
				!state.isEditCustomPermissionModalOpen;
		},
		openIsEditCustomPermissionModalOpen: (state) => {
			state.isEditCustomPermissionModalOpen = true;
		},
		closeIsEditCustomPermissionModalOpen: (state, action) => {
			state.isEditCustomPermissionModalOpen = false;
		},
		toggleIsDeleteCustomPermissionModalOpen: (state) => {
			state.isDeleteCustomPermissionModalOpen +=
				!state.isDeleteCustomPermissionModalOpen;
		},
		openIsDeleteCustomPermissionModalOpen: (state) => {
			state.isDeleteCustomPermissionModalOpen = true;
		},
		closeIsDeleteCustomPermissionModalOpen: (state, action) => {
			state.isDeleteCustomPermissionModalOpen = false;
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
} = appPermissionsManagementSlice.actions;

export const selectIsAddCustomPermissionModalOpen = (state) =>
	state.appPermissionsManagement.isAddCustomPermissionModalOpen;

export const selectIsEditCustomPermissionModalOpen = (state) =>
	state.appPermissionsManagement.isEditCustomPermissionModalOpen;

export const selectIsDeleteCustomPermissionModalOpen = (state) =>
	state.appPermissionsManagement.isDeleteCustomPermissionModalOpen;

export default appPermissionsManagementSlice.reducer;
