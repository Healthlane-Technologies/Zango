import { configureStore } from '@reduxjs/toolkit';

import platformReducer from '../pages/platform/slice';
import platformUserManagementReducer from '../pages/platformUserManagement/slice';
import appUserManagementReducer from '../pages/appUserManagement/slice';
import appConfigurationReducer from '../pages/appConfiguration/slice';
import appThemeConfigurationReducer from '../pages/appThemeConfiguration/slice';

export default configureStore({
	reducer: {
		platform: platformReducer,
		platformUserManagement: platformUserManagementReducer,
		appUserManagement: appUserManagementReducer,
		appConfiguration: appConfigurationReducer,
		appThemeConfiguration: appThemeConfigurationReducer,
	},
});
