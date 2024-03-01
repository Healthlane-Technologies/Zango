import { configureStore } from '@reduxjs/toolkit';

import platformReducer from '../pages/platform/slice';
import platformUserManagementReducer from '../pages/platformUserManagement/slice';
import appUserRolesReducer from '../pages/appUserRoles/slice';
import appUserManagementReducer from '../pages/appUserManagement/slice';
import appTaskManagementReducer from '../pages/appTaskManagement/slice';
import appPermissionsManagementReducer from '../pages/appPermissionsManagement/slice';
import appPoliciesManagementReducer from '../pages/appPoliciesManagement/slice';
import appConfigurationReducer from '../pages/appConfiguration/slice';
import appThemeConfigurationReducer from '../pages/appThemeConfiguration/slice';
import appPackagesManagementReducer from '../pages/appPackagesManagement/slice';
import appChatbotReducer from '../pages/app/slice';

export default configureStore({
	reducer: {
		platform: platformReducer,
		platformUserManagement: platformUserManagementReducer,
		appUserRoles: appUserRolesReducer,
		appUserManagement: appUserManagementReducer,
		appTaskManagement: appTaskManagementReducer,
		appPermissionsManagement: appPermissionsManagementReducer,
		appPoliciesManagement: appPoliciesManagementReducer,
		appConfiguration: appConfigurationReducer,
		appThemeConfiguration: appThemeConfigurationReducer,
		appPackagesManagement: appPackagesManagementReducer,
		appChatbot: appChatbotReducer,
	},
});
