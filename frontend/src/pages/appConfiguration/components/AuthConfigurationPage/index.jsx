import React from 'react';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import AuthConfiguration from '../AppConfiguration/AuthConfiguration';

export default function AuthConfigurationPage() {
	return (
		<div className="flex min-h-screen grow flex-col bg-[#F8FAFC]">
			{/* Header */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px]">
				<div className="flex items-center justify-between">
					<div>
						<BreadCrumbs />
						<div className="flex items-center gap-[12px] mt-[8px]">
							<div className="flex h-[32px] w-[32px] items-center justify-center rounded-[6px] bg-[#346BD4]">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
									<path d="M12 8V6C12 3.79086 10.2091 2 8 2C5.79086 2 4 3.79086 4 6V8M3 8H13C13.5523 8 14 8.44772 14 9V14C14 14.5523 13.5523 15 13 15H3C2.44772 15 2 14.5523 2 14V9C2 8.44772 2.44772 8 3 8Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							</div>
							<div>
								<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
									Authentication Configuration
								</h1>
								<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
									Manage login methods, session policies, and security settings for your application
								</p>
							</div>
						</div>
					</div>
				</div>
			</div>

			{/* Content */}
			<div className="flex-1 px-[40px] py-[32px]">
				<AuthConfiguration />
			</div>
		</div>
	);
}