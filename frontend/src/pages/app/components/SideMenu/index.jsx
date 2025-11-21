import { NavLink } from 'react-router-dom';
import { ReactComponent as AppSettingsIcon } from '../../../../assets/images/svg/app-settings-icon.svg';
import { ReactComponent as AppUserManagementIcon } from '../../../../assets/images/svg/app-user-management-icon.svg';
import { ReactComponent as AppSecretsIcon } from '../../../../assets/images/svg/app-secrets-icon.svg';
import { ReactComponent as DashboardIcon } from '../../../../assets/images/svg/app-settings-icon.svg';

export default function SideMenu() {
	return (
		<div
			data-cy="menu_section"
			className="z-[3] w-[88px] min-w-[88px] max-w-[88px] bg-secondary pt-[12px] sticky top-0 overflow-y-auto"
			style={{ height: 'calc(100vh - var(--navHeight, 64px))' }}
		>
			<NavLink
				data-cy="app_settings"
				to={`app-settings/app-configuration/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<AppSettingsIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					App Settings
				</span>
			</NavLink>
			<NavLink
				data-cy="code"
				to={`code/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<path d="M14 2L14 8C14 8.55228 14.4477 9 15 9L21 9" stroke="#26210F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
					<path d="M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H14L19 8V19C19 20.1046 18.1046 21 17 21Z" stroke="#26210F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
					<path d="M9 13H15" stroke="#26210F" strokeWidth="2" strokeLinecap="round"/>
					<path d="M9 17H12" stroke="#26210F" strokeWidth="2" strokeLinecap="round"/>
				</svg>
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Code
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
					App Users
				</span>
			</NavLink>
			<NavLink
				data-cy="logs"
				to={`logs/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<path d="M4 6H20M4 10H20M4 14H20M4 18H12" stroke="#26210F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
					<circle cx="17" cy="17" r="3" stroke="#26210F" strokeWidth="2"/>
					<path d="M19.5 19.5L21 21" stroke="#26210F" strokeWidth="2" strokeLinecap="round"/>
				</svg>
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Logs
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

		</div>
	);
}
