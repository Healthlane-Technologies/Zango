import { createSlice } from '@reduxjs/toolkit';

export const appUserRolesSlice = createSlice({
	name: 'appUserRoles',
	initialState: {
		isAddNewUserRolesModalOpen: false,
		isEditUserRolesDetailModalOpen: false,
		isDeactivateUserRolesModalOpen: false,
	},
	reducers: {
		toggleIsAddNewUserRolesModalOpen: (state) => {
			state.isAddNewUserRolesModalOpen += !state.isAddNewUserRolesModalOpen;
		},
		openIsAddNewUserRolesModalOpen: (state) => {
			state.isAddNewUserRolesModalOpen = true;
		},
		closeIsAddNewUserRolesModalOpen: (state, action) => {
			state.isAddNewUserRolesModalOpen = false;
		},
		toggleIsEditUserRolesDetailModalOpen: (state) => {
			state.isEditUserRolesDetailModalOpen +=
				!state.isEditUserRolesDetailModalOpen;
		},
		openIsEditUserRolesDetailModalOpen: (state) => {
			state.isEditUserRolesDetailModalOpen = true;
		},
		closeIsEditUserRolesDetailModalOpen: (state, action) => {
			state.isEditUserRolesDetailModalOpen = false;
		},
		toggleIsDeactivateUserRolesModalOpen: (state) => {
			state.isDeactivateUserRolesModalOpen +=
				!state.isDeactivateUserRolesModalOpen;
		},
		openIsDeactivateUserRolesModalOpen: (state) => {
			state.isDeactivateUserRolesModalOpen = true;
		},
		closeIsDeactivateUserRolesModalOpen: (state, action) => {
			state.isDeactivateUserRolesModalOpen = false;
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
} = appUserRolesSlice.actions;

export const selectIsAddNewUserRolesModalOpen = (state) =>
	state.appUserRoles.isAddNewUserRolesModalOpen;

export const selectIsEditUserRolesDetailModalOpen = (state) =>
	state.appUserRoles.isEditUserRolesDetailModalOpen;

export const selectIsDeactivateUserRolesModalOpen = (state) =>
	state.appUserRoles.isDeactivateUserRolesModalOpen;

export default appUserRolesSlice.reducer;
