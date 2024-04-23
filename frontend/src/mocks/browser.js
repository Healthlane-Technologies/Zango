// src/mocks/browser.js
import { setupWorker } from 'msw';
import { handlers } from './handlers';
import { platformAppHandlers } from './platformAppHandlers';
import { platformUsersMangementHandlers } from './platformUsersMangementHandlers';
import { appUserRolesHandlers } from './appUserRolesHandlers';
import { appUsersManagementHandlers } from './appUsersManagementHandlers';
import { appPermissionsManagementHandlers } from './appPermissionsManagementHandlers';
import { appPoliciesManagementHandlers } from './appPoliciesManagementHandlers';
import { appTasksManagementHandlers } from './appTasksManagementHandlers';
import { appConfigurationHandlers } from './appConfigurationHandlers';
import { appThemeConfigurationHandlers } from './appThemeConfigurationHandlers';
import { appPackagesManagementHandlers } from './appPackagesManagementHandlers';
import { appInitialHandlers } from './appInitialHandlers';
import { appChatbotHandlers } from './appChatbotHandlers';
import { appAuditLogsHandlers } from './appAuditLogsHandlers';

// This configures a Service Worker with the given request handlers.
export const worker = setupWorker(
	...handlers,
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
	...appAuditLogsHandlers
);
