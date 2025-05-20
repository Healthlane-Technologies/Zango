// src/mocks/browser.js
import { setupWorker } from 'msw';
import { appAuditLogsHandlers } from './appAuditLogsHandlers';
import { appChatbotHandlers } from './appChatbotHandlers';
import { appConfigurationHandlers } from './appConfigurationHandlers';
import { appInitialHandlers } from './appInitialHandlers';
import { appPackagesManagementHandlers } from './appPackagesManagementHandlers';
import { appPermissionsManagementHandlers } from './appPermissionsManagementHandlers';
import { appPoliciesManagementHandlers } from './appPoliciesManagementHandlers';
import { appTasksManagementHandlers } from './appTasksManagementHandlers';
import { appThemeConfigurationHandlers } from './appThemeConfigurationHandlers';
import { appUserRolesHandlers } from './appUserRolesHandlers';
import { appUsersManagementHandlers } from './appUsersManagementHandlers';
import { platformAppHandlers } from './platformAppHandlers';
import { platformUsersMangementHandlers } from './platformUsersMangementHandlers';
import { appAccessLogsHandlers } from './appAccessLogsHandlers';
import { appReleasesHandlers } from './appReleasesHandlers';
import { appSecretsHandlers } from './appSecretsHandlers';

// This configures a Service Worker with the given request handlers.
export const worker = setupWorker(
	...platformAppHandlers,
	...platformUsersMangementHandlers,
	...appUserRolesHandlers,
	...appUsersManagementHandlers,
	...appPermissionsManagementHandlers,
	...appPoliciesManagementHandlers,
	...appTasksManagementHandlers,
	...appConfigurationHandlers,
	...appThemeConfigurationHandlers,
	...appPackagesManagementHandlers,
	...appInitialHandlers,
	...appChatbotHandlers,
	...appAuditLogsHandlers,
	...appAccessLogsHandlers,
	...appReleasesHandlers,
	...appSecretsHandlers
);
