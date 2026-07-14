import { NavLink } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ReactComponent as AppSettingsIcon } from '../../../../assets/images/svg/app-settings-icon.svg';
import { ReactComponent as AppUserManagementIcon } from '../../../../assets/images/svg/app-user-management-icon.svg';
import { ReactComponent as AppSecretsIcon } from '../../../../assets/images/svg/app-secrets-icon.svg';
import { ReactComponent as DashboardIcon } from '../../../../assets/images/svg/app-settings-icon.svg';
import { selectAppConfigurationData } from '../../../appConfiguration/slice';

export default function SideMenu() {
	const appConfigurationData = useSelector(selectAppConfigurationData);
	const isSuspended =
		(appConfigurationData?.app?.status ||
			appConfigurationData?.status) === 'suspended';

	return (
		<div
			data-cy="menu_section"
			className="z-[3] flex w-[88px] min-w-[88px] max-w-[88px] flex-col bg-secondary pt-[12px] sticky top-0 overflow-y-auto"
			style={{ height: 'calc(100vh - var(--navHeight, 64px))' }}
		>
			{isSuspended ? (
				<div
					className="mx-[8px] mb-[10px] flex flex-col items-center gap-[4px] rounded-[8px] border px-[4px] py-[8px]"
					style={{
						backgroundColor: '#FEF6E7',
						borderColor: 'rgba(218,144,17,0.32)',
					}}
					title="This app is suspended — end users see a 404 page"
					data-cy="app_suspended_badge"
				>
					<svg
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="#8A5A07"
						strokeWidth="2"
						strokeLinecap="round"
						strokeLinejoin="round"
					>
						<rect x="3" y="11" width="18" height="10" rx="2" />
						<path d="M7 11V7a5 5 0 0 1 10 0v4" />
					</svg>
					<span
						className="text-center font-lato text-[9px] font-bold uppercase leading-[11px] tracking-[0.06em]"
						style={{ color: '#8A5A07' }}
					>
						Suspended
					</span>
				</div>
			) : null}
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
				data-cy="ai"
				to={`ai/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<path d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z" stroke="#26210F" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
				</svg>
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					AI
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
