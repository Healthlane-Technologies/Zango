import { configureStore } from '@reduxjs/toolkit';
import appChatbotReducer from '../pages/app/slice';
import appAccessLogsReducer from '../pages/appAccessLogs/slice';
import appApplicationObjectsLogsReducer from '../pages/appApplicationObjectsLogs/slice';
import appConfigurationReducer from '../pages/appConfiguration/slice';
import appFrameworkObjectsLogsReducer from '../pages/appFrameworkObjectsLogs/slice';
import appPackagesManagementReducer from '../pages/appPackagesManagement/slice';
import appPermissionsManagementReducer from '../pages/appPermissionsManagement/slice';
import appPoliciesManagementReducer from '../pages/appPoliciesManagement/slice';
import appTaskManagementReducer from '../pages/appTaskManagement/slice';
import appThemeConfigurationReducer from '../pages/appThemeConfiguration/slice';
import appUserManagementReducer from '../pages/appUserManagement/slice';
import appUserRolesReducer from '../pages/appUserRoles/slice';
import platformReducer from '../pages/platform/slice';
import platformUserManagementReducer from '../pages/platformUserManagement/slice';
import appReleasesReducer  from '../pages/appReleasesRoutes/slice/Index';
import appSecretsReducer from '../pages/appSecretsRoutes/slice/Index';

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
		appApplicationObjectsLogs: appApplicationObjectsLogsReducer,
		appFrameworkObjectsLogs: appFrameworkObjectsLogsReducer,
		appAccessLogs: appAccessLogsReducer,
		appReleases : appReleasesReducer, 
		appSecrets : appSecretsReducer,
	},
});
