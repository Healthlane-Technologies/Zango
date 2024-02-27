import { createSlice } from '@reduxjs/toolkit';

export const appPackagesManagementSlice = createSlice({
	name: 'appPackagesManagement',
	initialState: {
		isConfigurePackageModalOpen: false,
		isInstallPackageModalOpen: false,
		rerenderPage: false,
		appPackagesManagementData: null,
		appPackagesManagementFormData: null,
		appPackagesManagementTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
	},
	reducers: {
		toggleIsConfigurePackageModalOpen: (state) => {
			state.isConfigurePackageModalOpen += !state.isConfigurePackageModalOpen;
		},
		openIsConfigurePackageModalOpen: (state, action) => {
			state.isConfigurePackageModalOpen = true;
			state.appPackagesManagementFormData = action.payload;
		},
		closeIsConfigurePackageModalOpen: (state) => {
			state.isConfigurePackageModalOpen = false;
			state.appPackagesManagementFormData = null;
		},
		toggleIsInstallPackageModalOpen: (state) => {
			state.isInstallPackageModalOpen += !state.isInstallPackageModalOpen;
		},
		openIsInstallPackageModalOpen: (state, action) => {
			state.isInstallPackageModalOpen = true;
			state.appPackagesManagementFormData = action.payload;
		},
		closeIsInstallPackageModalOpen: (state) => {
			state.isInstallPackageModalOpen = false;
			state.appPackagesManagementFormData = null;
		},
		setAppPackagesManagementData: (state, action) => {
			state.appPackagesManagementData = action.payload;
		},
		setAppPackagesManagementTableData: (state, action) => {
			state.appPackagesManagementTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsConfigurePackageModalOpen,
	openIsConfigurePackageModalOpen,
	closeIsConfigurePackageModalOpen,
	toggleIsInstallPackageModalOpen,
	openIsInstallPackageModalOpen,
	closeIsInstallPackageModalOpen,
	setAppPackagesManagementData,
	setAppPackagesManagementTableData,
	toggleRerenderPage,
} = appPackagesManagementSlice.actions;

export const selectIsConfigurePackageModalOpen = (state) =>
	state.appPackagesManagement.isConfigurePackageModalOpen;

export const selectIsInstallPackageModalOpen = (state) =>
	state.appPackagesManagement.isInstallPackageModalOpen;

export const selectRerenderPage = (state) =>
	state.appPackagesManagement.rerenderPage;

export const selectAppPackagesManagementData = (state) =>
	state.appPackagesManagement.appPackagesManagementData;

export const selectAppPackagesManagementTableData = (state) =>
	state.appPackagesManagement.appPackagesManagementTableData;

export const selectAppPackagesManagementFormData = (state) =>
	state.appPackagesManagement.appPackagesManagementFormData;

export default appPackagesManagementSlice.reducer;
