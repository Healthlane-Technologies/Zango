import { createSlice } from '@reduxjs/toolkit';

export const appPoliciesManagementSlice = createSlice({
	name: 'appPoliciesManagement',
	initialState: {
		isAddPolicyModalOpen: false,
		isEditPolicyModalOpen: false,
		isViewPolicyModalOpen: false,
		isDeletePolicyModalOpen: false,
	},
	reducers: {
		toggleIsAddPolicyModalOpen: (state) => {
			state.isAddPolicyModalOpen += !state.isAddPolicyModalOpen;
		},
		openIsAddPolicyModalOpen: (state) => {
			state.isAddPolicyModalOpen = true;
		},
		closeIsAddPolicyModalOpen: (state, action) => {
			state.isAddPolicyModalOpen = false;
		},
		toggleIsEditPolicyModalOpen: (state) => {
			state.isEditPolicyModalOpen += !state.isEditPolicyModalOpen;
		},
		openIsEditPolicyModalOpen: (state) => {
			state.isEditPolicyModalOpen = true;
		},
		closeIsEditPolicyModalOpen: (state, action) => {
			state.isEditPolicyModalOpen = false;
		},
		toggleIsViewPolicyModalOpen: (state) => {
			state.isViewPolicyModalOpen += !state.isViewPolicyModalOpen;
		},
		openIsViewPolicyModalOpen: (state) => {
			state.isViewPolicyModalOpen = true;
		},
		closeIsViewPolicyModalOpen: (state, action) => {
			state.isViewPolicyModalOpen = false;
		},
		toggleIsDeletePolicyModalOpen: (state) => {
			state.isDeletePolicyModalOpen += !state.isDeletePolicyModalOpen;
		},
		openIsDeletePolicyModalOpen: (state) => {
			state.isDeletePolicyModalOpen = true;
		},
		closeIsDeletePolicyModalOpen: (state, action) => {
			state.isDeletePolicyModalOpen = false;
		},
	},
});

export const {
	toggleIsAddPolicyModalOpen,
	openIsAddPolicyModalOpen,
	closeIsAddPolicyModalOpen,
	toggleIsEditPolicyModalOpen,
	openIsEditPolicyModalOpen,
	closeIsEditPolicyModalOpen,
	toggleIsViewPolicyModalOpen,
	openIsViewPolicyModalOpen,
	closeIsViewPolicyModalOpen,
	toggleIsDeletePolicyModalOpen,
	openIsDeletePolicyModalOpen,
	closeIsDeletePolicyModalOpen,
} = appPoliciesManagementSlice.actions;

export const selectIsAddPolicyModalOpen = (state) =>
	state.appPoliciesManagement.isAddPolicyModalOpen;

export const selectIsEditPolicyModalOpen = (state) =>
	state.appPoliciesManagement.isEditPolicyModalOpen;

export const selectIsViewPolicyModalOpen = (state) =>
	state.appPoliciesManagement.isViewPolicyModalOpen;

export const selectIsDeletePolicyModalOpen = (state) =>
	state.appPoliciesManagement.isDeletePolicyModalOpen;

export default appPoliciesManagementSlice.reducer;
