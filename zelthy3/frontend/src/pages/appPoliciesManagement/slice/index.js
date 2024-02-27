import { createSlice } from '@reduxjs/toolkit';

export const appPoliciesManagementSlice = createSlice({
	name: 'appPoliciesManagement',
	initialState: {
		isAddPolicyModalOpen: false,
		isEditPolicyModalOpen: false,
		isViewPolicyModalOpen: false,
		isEditViewPolicy: false,
		isDeletePolicyModalOpen: false,
		rerenderPage: false,
		appPoliciesManagementData: null,
		appPoliciesManagementFormData: null,
		appPoliciesManagementTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
	},
	reducers: {
		toggleIsAddPolicyModalOpen: (state) => {
			state.isAddPolicyModalOpen += !state.isAddPolicyModalOpen;
		},
		openIsAddPolicyModalOpen: (state, action) => {
			state.isAddPolicyModalOpen = true;
			state.appPoliciesManagementFormData = action.payload;
		},
		closeIsAddPolicyModalOpen: (state) => {
			state.isAddPolicyModalOpen = false;
			state.appPoliciesManagementFormData = null;
		},
		toggleIsEditPolicyModalOpen: (state) => {
			state.isEditPolicyModalOpen += !state.isEditPolicyModalOpen;
		},
		openIsEditPolicyModalOpen: (state, action) => {
			state.isEditPolicyModalOpen = true;
			state.appPoliciesManagementFormData = action.payload;
		},
		closeIsEditPolicyModalOpen: (state) => {
			state.isEditPolicyModalOpen = false;
			state.appPoliciesManagementFormData = null;
		},
		toggleIsViewPolicyModalOpen: (state) => {
			state.isViewPolicyModalOpen += !state.isViewPolicyModalOpen;
		},
		openIsViewPolicyModalOpen: (state, action) => {
			state.isViewPolicyModalOpen = true;
			state.appPoliciesManagementFormData = action.payload;
		},
		closeIsViewPolicyModalOpen: (state) => {
			state.isViewPolicyModalOpen = false;
			state.isEditViewPolicy = false;
			state.appPoliciesManagementFormData = null;
		},
		toggleIsEditViewPolicy: (state) => {
			state.isEditViewPolicy = !state.isEditViewPolicy;
		},
		toggleIsDeletePolicyModalOpen: (state) => {
			state.isDeletePolicyModalOpen += !state.isDeletePolicyModalOpen;
		},
		openIsDeletePolicyModalOpen: (state, action) => {
			state.isDeletePolicyModalOpen = true;
			state.appPoliciesManagementFormData = action.payload;
		},
		closeIsDeletePolicyModalOpen: (state) => {
			state.isDeletePolicyModalOpen = false;
			state.appPoliciesManagementFormData = null;
		},
		setAppPoliciesManagementData: (state, action) => {
			state.appPoliciesManagementData = action.payload;
		},
		setAppPoliciesManagementTableData: (state, action) => {
			state.appPoliciesManagementTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
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
	toggleIsEditViewPolicy,
	toggleIsDeletePolicyModalOpen,
	openIsDeletePolicyModalOpen,
	closeIsDeletePolicyModalOpen,
	setAppPoliciesManagementData,
	setAppPoliciesManagementTableData,
	toggleRerenderPage,
} = appPoliciesManagementSlice.actions;

export const selectIsAddPolicyModalOpen = (state) =>
	state.appPoliciesManagement.isAddPolicyModalOpen;

export const selectIsEditPolicyModalOpen = (state) =>
	state.appPoliciesManagement.isEditPolicyModalOpen;

export const selectIsViewPolicyModalOpen = (state) =>
	state.appPoliciesManagement.isViewPolicyModalOpen;

export const selectIsEditViewPolicy = (state) =>
	state.appPoliciesManagement.isEditViewPolicy;

export const selectIsDeletePolicyModalOpen = (state) =>
	state.appPoliciesManagement.isDeletePolicyModalOpen;

export const selectRerenderPage = (state) =>
	state.appPoliciesManagement.rerenderPage;

export const selectAppPoliciesManagementData = (state) =>
	state.appPoliciesManagement.appPoliciesManagementData;

export const selectAppPoliciesManagementTableData = (state) =>
	state.appPoliciesManagement.appPoliciesManagementTableData;

export const selectAppPoliciesManagementFormData = (state) =>
	state.appPoliciesManagement.appPoliciesManagementFormData;

export default appPoliciesManagementSlice.reducer;
