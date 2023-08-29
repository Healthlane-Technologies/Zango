import { createSlice } from '@reduxjs/toolkit';

export const appTaskManagementSlice = createSlice({
	name: 'appTaskManagement',
	initialState: {
		isUpdatePolicyModalOpen: false,
		isRemoveAllPoliciesModalOpen: false,
	},
	reducers: {
		toggleIsUpdatePolicyModalOpen: (state) => {
			state.isUpdatePolicyModalOpen += !state.isUpdatePolicyModalOpen;
		},
		openIsUpdatePolicyModalOpen: (state) => {
			state.isUpdatePolicyModalOpen = true;
		},
		closeIsUpdatePolicyModalOpen: (state, action) => {
			state.isUpdatePolicyModalOpen = false;
		},
		toggleIsRemoveAllPoliciesModalOpen: (state) => {
			state.isRemoveAllPoliciesModalOpen += !state.isRemoveAllPoliciesModalOpen;
		},
		openIsRemoveAllPoliciesModalOpen: (state) => {
			state.isRemoveAllPoliciesModalOpen = true;
		},
		closeIsRemoveAllPoliciesModalOpen: (state, action) => {
			state.isRemoveAllPoliciesModalOpen = false;
		},
	},
});

export const {
	toggleIsUpdatePolicyModalOpen,
	openIsUpdatePolicyModalOpen,
	closeIsUpdatePolicyModalOpen,
	toggleIsRemoveAllPoliciesModalOpen,
	openIsRemoveAllPoliciesModalOpen,
	closeIsRemoveAllPoliciesModalOpen,
} = appTaskManagementSlice.actions;

export const selectIsUpdatePolicyModalOpen = (state) =>
	state.appTaskManagement.isUpdatePolicyModalOpen;

export const selectIsRemoveAllPoliciesModalOpen = (state) =>
	state.appTaskManagement.isRemoveAllPoliciesModalOpen;

export default appTaskManagementSlice.reducer;
