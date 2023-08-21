import { configureStore } from '@reduxjs/toolkit';

import platformReducer from '../pages/platform/slice';
import userManagementReducer from '../pages/userManagement/slice';

export default configureStore({
	reducer: {
		platform: platformReducer,
		userManagement: userManagementReducer,
	},
});
