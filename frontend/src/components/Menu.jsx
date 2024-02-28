import React from 'react';
import { Link } from 'react-router-dom';

import { useDashboard } from '../context/DashboardContextProvider';

const Menu = ({ MenuItems }) => {
	const { userRoleData } = useDashboard();
	return (
		<div className="complete-hidden-scroll-style flex grow flex-col overflow-y-auto md:hidden">
			<header className="px-6 pt-30 pb-8 font-invention-app text-xl font-bold">
				Menu
			</header>

			<div className="flex flex-col gap-1">
				{MenuItems.map((item, key) => {
					return userRoleData?.userRoleCode === 'doctor-delegate' &&
						item.label === 'Delegate' ? null : (
						<React.Fragment key={key}>
							<MenuItem label={item.label} link={item.link} />
						</React.Fragment>
					);
				})}
				<a href="/logout">
					<div className="flex items-center justify-between bg-off-white py-6 pl-6 pr-12 ">
						<span className="text-base font-bold text-dark-gray ">Log Out</span>
					</div>
				</a>
			</div>
		</div>
	);
};

const MenuItem = ({ label, link }) => {
	return (
		<Link to={link}>
			<div className="flex items-center justify-between bg-off-white py-6 pl-6 pr-12 ">
				<span className="font-invention-app text-base font-bold text-dark-gray ">
					{label}
				</span>
			</div>
		</Link>
	);
};

export default Menu;
