import { Link, NavLink } from 'react-router-dom';
import { ReactComponent as EachSideMenuIcon } from '../../../../assets/images/svg/each-side-menu-icon.svg';
import SideMenuDropdown from './SideMenuDropdown';

export default function SideMenu() {
	return (
		<div className="z-[3] w-[88px] min-w-[88px] max-w-[88px] bg-secondary pt-[12px]">
			<NavLink
				to={`user-roles/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<EachSideMenuIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					User Roles
				</span>
			</NavLink>
			<NavLink
				to={`user-management/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<EachSideMenuIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					User Management
				</span>
			</NavLink>
			<SideMenuDropdown
				Icon={EachSideMenuIcon}
				label="App Settings"
				sublinks={[
					{
						url: `app-settings/app-configuration/`,
						label: 'App Configuration',
					},
					{
						url: `app-settings/app-theme-configuration/`,
						label: 'App Theme Configuration',
					},
				]}
			/>
			<NavLink
				to={`permission-management/policies/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<EachSideMenuIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Policies
				</span>
			</NavLink>

			{/* <SideMenuDropdown
				Icon={EachSideMenuIcon}
				label="Permission Management"
				sublinks={[
					// {
					// 	url: `permission-management/permissions/`,
					// 	label: 'Permissions',
					// },
					{
						url: `permission-management/policies/`,
						label: 'Policies',
					},
				]}
			/> */}
			<NavLink
				to={`tasks-management/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<EachSideMenuIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Tasks Management
				</span>
			</NavLink>
			<NavLink
				to={`packages-management/`}
				className={({ isActive, isPending }) =>
					`flex flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
						isPending ? 'bg-transparent' : isActive ? 'bg-[#d3c9a4]' : ''
					}`
				}
			>
				<EachSideMenuIcon />
				<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
					Packages Management
				</span>
			</NavLink>
		</div>
	);
}
