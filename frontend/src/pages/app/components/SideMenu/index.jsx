import { NavLink } from 'react-router-dom';
import { ReactComponent as AppPackagesIcon } from '../../../../assets/images/svg/app-packages-icon.svg';
import { ReactComponent as AppPolicyIcon } from '../../../../assets/images/svg/app-policy-icon.svg';
import { ReactComponent as AppSettingsIcon } from '../../../../assets/images/svg/app-settings-icon.svg';
import { ReactComponent as AppTasksIcon } from '../../../../assets/images/svg/app-tasks-icon.svg';
import { ReactComponent as AppUserManagementIcon } from '../../../../assets/images/svg/app-user-management-icon.svg';
import { ReactComponent as AppUserRoleIcon } from '../../../../assets/images/svg/app-user-role-icon.svg';
import { ReactComponent as AppSecretsIcon } from '../../../../assets/images/svg/app-secrets-icon.svg';
import SideMenuDropdown from './SideMenuDropdown';

export default function SideMenu() {
	return (
		<div
			data-cy="menu_section"
			className="z-[3] w-[88px] min-w-[88px] max-w-[88px] bg-secondary pt-[12px]"
		>
			<SideMenuDropdown
				Icon={AppSettingsIcon}
				label="App Settings"
				sublinks={[
					{
						url: `app-settings/app-configuration/`,
						label: 'App Configuration',
						dataCy: 'app_configuration',
					},
					{
						url: `app-settings/app-theme-configuration/`,
						label: 'App Theme Configuration',
						dataCy: 'app_theme_configuration',
					},
				]}
			/>
			<NavLink
				data-cy="user_roles"
				to={`user-roles/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppUserRoleIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					User Roles
				</span>
			</NavLink>
			<NavLink
				data-cy="user_management"
				to={`user-management/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppUserManagementIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					User
				</span>
			</NavLink>
			<NavLink
				data-cy="policies"
				to={`permission-management/policies/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppPolicyIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Policies
				</span>
			</NavLink>
			<NavLink
				data-cy="task_management"
				to={`tasks-management/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppTasksIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Tasks
				</span>
			</NavLink>
			<NavLink
				data-cy="packages"
				to={`packages-management/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppPackagesIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Packages
				</span>
			</NavLink>
			<SideMenuDropdown
				Icon={AppSettingsIcon}
				label="Audit Logs"
				sublinks={[
					{
						url: `audit-logs/application-objects-logs`,
						label: 'Application Objects',
						dataCy: 'application_objects',
					},
					{
						url: `audit-logs/framework-objects-logs`,
						label: 'Framework Objects',
						dataCy: 'framework_objects',
					},
				]}
			/>
			<NavLink
				to={`access-logs/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppSettingsIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Access Logs
				</span>
			</NavLink>

			<NavLink
				to={`Releases/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppSettingsIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Releases
				</span>
			</NavLink>

			<NavLink
				to={`Secrets/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppSecretsIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Secrets
				</span>
			</NavLink>
		</div>
	);
}
