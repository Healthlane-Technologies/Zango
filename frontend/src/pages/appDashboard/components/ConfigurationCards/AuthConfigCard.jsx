import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as ShieldIcon } from '../../../../assets/images/svg/app-policy-icon.svg';
import { ReactComponent as ArrowRightIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import useApi from '../../../../hooks/useApi';

export default function AuthConfigCard({ appId }) {
	const [authConfig, setAuthConfig] = useState(null);
	const [isLoading, setIsLoading] = useState(true);
	const triggerApi = useApi();

	useEffect(() => {
		const fetchAuthConfig = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/authentication/`,
				type: 'GET',
				loader: false,
			});
			
			if (success && response) {
				setAuthConfig(response);
			}
			setIsLoading(false);
		};

		fetchAuthConfig();
	}, [appId]);

	const getActiveLoginMethods = () => {
		if (!authConfig) return [];
		const methods = [];
		if (authConfig.enable_password_login) methods.push('Password');
		if (authConfig.enable_otp_login) methods.push('OTP');
		if (authConfig.enable_sso_login) methods.push('SSO');
		if (authConfig.enable_oidc_login) methods.push('OIDC');
		return methods;
	};

	const activeLoginMethods = getActiveLoginMethods();
	const isConfigured = activeLoginMethods.length > 0;

	if (isLoading) {
		return (
			<div className="flex flex-col rounded-[12px] border border-[#DDE2E5] bg-white p-[24px]">
				<div className="animate-pulse">
					<div className="mb-[20px] h-[60px] bg-gray-200 rounded"></div>
					<div className="space-y-3">
						<div className="h-4 bg-gray-200 rounded"></div>
						<div className="h-4 bg-gray-200 rounded"></div>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="flex flex-col rounded-[12px] border border-[#DDE2E5] bg-white p-[24px]">
			{/* Card Header */}
			<div className="mb-[20px] flex items-start justify-between">
				<div className="flex items-center gap-[12px]">
					<div className="rounded-[8px] bg-[#FEF3C7] p-[10px]">
						<ShieldIcon className="h-[20px] w-[20px] text-[#F59E0B]" />
					</div>
					<div>
						<h3 className="font-source-sans-pro text-[18px] font-semibold text-[#212429]">
							Authentication
						</h3>
						<p className="font-lato text-[12px] text-[#6C747D]">
							Login methods & security
						</p>
					</div>
				</div>
				<span
					className={`rounded-[20px] px-[8px] py-[2px] text-[11px] font-medium ${
						isConfigured
							? 'bg-[#E4F9F2] text-[#2CBE90]'
							: 'bg-[#FFEDD5] text-[#EA580C]'
					}`}
				>
					{isConfigured ? 'Active' : 'Not Configured'}
				</span>
			</div>

			{/* Card Content */}
			<div className="mb-[20px] flex flex-col gap-[12px]">
				<div>
					<span className="font-lato text-[14px] text-[#6C747D]">
						Login Methods
					</span>
					{activeLoginMethods.length > 0 ? (
						<div className="mt-[4px] flex flex-wrap gap-[8px]">
							{activeLoginMethods.map((method) => (
								<span
									key={method}
									className="rounded-[4px] bg-[#F0F3F4] px-[8px] py-[4px] font-lato text-[12px] font-medium text-[#212429]"
								>
									{method}
								</span>
							))}
						</div>
					) : (
						<p className="mt-[4px] font-lato text-[14px] text-[#9CA3AF]">
							No login methods configured
						</p>
					)}
				</div>
				
				<div className="flex justify-between">
					<span className="font-lato text-[14px] text-[#6C747D]">
						Two-Factor Auth
					</span>
					<span className="font-lato text-[14px] font-medium text-[#212429]">
						{authConfig?.enable_two_factor_authentication ? 'Enabled' : 'Disabled'}
					</span>
				</div>

				<div className="flex justify-between">
					<span className="font-lato text-[14px] text-[#6C747D]">
						Max Sessions
					</span>
					<span className="font-lato text-[14px] font-medium text-[#212429]">
						{authConfig?.max_concurrent_sessions || 'Unlimited'}
					</span>
				</div>
			</div>

			{/* Card Footer */}
			<Link
				to={`/platform/apps/${appId}/app-settings/app-configuration/#auth`}
				className="mt-auto flex items-center justify-between rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] transition-colors hover:bg-[#F0F3F4]"
			>
				<span className="font-lato text-[14px] font-medium text-[#212429]">
					Configure Authentication
				</span>
				<ArrowRightIcon className="h-[16px] w-[16px] text-[#6C747D]" />
			</Link>
		</div>
	);
}