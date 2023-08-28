import { createSlice } from '@reduxjs/toolkit';

export const platformUserManagementSlice = createSlice({
	name: 'platformUserManagement',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
	},
	reducers: {
		toggleIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen += !state.isAddNewUserModalOpen;
		},
		openIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = true;
		},
		closeIsAddNewUserModalOpen: (state, action) => {
			state.isAddNewUserModalOpen = false;
		},
		toggleIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen += !state.isEditUserDetailModalOpen;
		},
		openIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = true;
		},
		closeIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = false;
		},
		toggleIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen += !state.isDeactivateUserModalOpen;
		},
		openIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = true;
		},
		closeIsDeactivateUserModalOpen: (state, action) => {
			state.isDeactivateUserModalOpen = false;
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
} = platformUserManagementSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.platformUserManagement.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.platformUserManagement.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.platformUserManagement.isDeactivateUserModalOpen;

export default platformUserManagementSlice.reducer;
