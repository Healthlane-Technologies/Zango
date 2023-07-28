import { configureStore } from '@reduxjs/toolkit';

import platformReducer from '../pages/platform/slice';

export default configureStore({
	reducer: {
		platform: platformReducer,
	},
});
