import { createSlice } from '@reduxjs/toolkit';

export const appChatbotSlice = createSlice({
	name: 'appChatbot',
	initialState: {
		isDraggablePopoverOpen: false,
		popOverLink: '',
	},
	reducers: {
		toggleIsDraggablePopoverOpen: (state) => {
			state.isDraggablePopoverOpen += !state.isDraggablePopoverOpen;
		},
		openIsDraggablePopoverOpen: (state) => {
			state.isDraggablePopoverOpen = true;
		},
		closeIsDraggablePopoverOpen: (state) => {
			state.isDraggablePopoverOpen = false;
		},
		setPopOverLink: (state, action) => {
			state.popOverLink = action.payload;
		}
	},
});

export const {
	toggleIsDraggablePopoverOpen,
	openIsDraggablePopoverOpen,
	closeIsDraggablePopoverOpen,
	setPopOverLink,
} = appChatbotSlice.actions;

export const selectIsDraggablePopoverOpen = (state) =>
	state.appChatbot.isDraggablePopoverOpen;

export const selectPopOverLink = (state) => state.appChatbot.popOverLink;

export default appChatbotSlice.reducer;
