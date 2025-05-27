import { createSlice } from '@reduxjs/toolkit';

export const appSecretsSlice = createSlice({
	name: 'appSecrets',
	initialState: {
		rerenderPage: false,
		appSecretsData: null,
		appSecretsFormData: null,
		appSecretsTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppSecretsDataEmpty: true,
		isAddSecretModalOpen: false,
		isEditSecretModalOpen: false,
	},
	reducers: {
		setAppSecretsData: (state, action) => {
			state.appSecretsData = action.payload;
			state.isAppSecretsDataEmpty =
				action.payload?.secrets?.records?.length ||
				state?.appSecretsTableData?.searchValue ||
				state?.appSecretsTableData?.columns?.length
					? false
					: true;
		},
		setAppSecretsTableData: (state, action) => {
			state.appSecretsTableData = action.payload;
		},
		setAddSecretModalOpen: (state, action) => {
			state.isAddSecretModalOpen = action.payload;
		},
		setEditSecretModalOpen: (state, action) => {
			state.isEditSecretModalOpen = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
		setAppSecretsFormData: (state, action) => {
			state.appSecretsFormData = action.payload;
		},
	},
});

export const {
	setAppSecretsData,
	setAppSecretsTableData,
	toggleRerenderPage,
	setAddSecretModalOpen,
	setFormData,
	clearFormData,
	setEditSecretModalOpen,
	setAppSecretsFormData,
} = appSecretsSlice.actions;


export const selectIsDeactivateUserRolesModalOpen = (state) =>
	state.appSecrets.isDeactivateUserRolesModalOpen;

export const selectRerenderPage = (state) => state.appSecrets.rerenderPage;

export const selectAppSecretsData = (state) =>
	state.appSecrets.appSecretsData;

export const selectAppSecretsFormData= (state) =>
	state.appSecrets.appSecretsFormData;

export const selectAppSecretsTableData = (state) =>
	state.appSecrets.appSecretsTableData;

export const selectIsAppSecretsDataEmpty = (state) =>
	state.appSecrets.isAppSecretsDataEmpty;

export const selectIsAddSecretModalOpen = (state) =>
	state.appSecrets.isAddSecretModalOpen;

export const selectIsEditSecretModalOpen = (state) =>
	state.appSecrets.isEditSecretModalOpen;


export default appSecretsSlice.reducer;
