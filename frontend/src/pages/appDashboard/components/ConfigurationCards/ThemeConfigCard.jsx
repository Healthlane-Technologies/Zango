import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as PaletteIcon } from '../../../../assets/images/svg/add-theme-icon.svg';
import { ReactComponent as ArrowRightIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import useApi from '../../../../hooks/useApi';

export default function ThemeConfigCard({ appId }) {
	const [themes, setThemes] = useState(null);
	const [isLoading, setIsLoading] = useState(true);
	const triggerApi = useApi();

	useEffect(() => {
		const fetchThemes = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/themes/`,
				type: 'GET',
				loader: false,
			});
			
			if (success && response) {
				setThemes(response.themes);
			}
			setIsLoading(false);
		};

		fetchThemes();
	}, [appId]);

	const activeTheme = themes?.find(theme => theme.is_active);
	const hasThemes = themes && themes.length > 0;

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
					<div className="rounded-[8px] bg-[#E4F9F2] p-[10px]">
						<PaletteIcon className="h-[20px] w-[20px] text-[#2CBE90]" />
					</div>
					<div>
						<h3 className="font-source-sans-pro text-[18px] font-semibold text-[#212429]">
							Theme Configuration
						</h3>
						<p className="font-lato text-[12px] text-[#6C747D]">
							Colors & typography
						</p>
					</div>
				</div>
				<span
					className={`rounded-[20px] px-[8px] py-[2px] text-[11px] font-medium ${
						hasThemes
							? 'bg-[#E4F9F2] text-[#2CBE90]'
							: 'bg-[#F3F4F6] text-[#6B7280]'
					}`}
				>
					{hasThemes ? `${themes.length} Theme${themes.length > 1 ? 's' : ''}` : 'No Themes'}
				</span>
			</div>

			{/* Card Content */}
			<div className="mb-[20px] flex flex-col gap-[12px]">
				{activeTheme ? (
					<>
						<div>
							<span className="font-lato text-[14px] text-[#6C747D]">
								Active Theme
							</span>
							<p className="mt-[2px] font-lato text-[16px] font-medium text-[#212429]">
								{activeTheme.name}
							</p>
						</div>
						
						{/* Color Preview */}
						<div>
							<span className="font-lato text-[14px] text-[#6C747D]">
								Theme Colors
							</span>
							<div className="mt-[8px] flex gap-[8px]">
								{activeTheme.config?.colors && (
									<>
										<div
											className="h-[32px] w-[32px] rounded-[4px] border border-[#DDE2E5]"
											style={{ backgroundColor: activeTheme.config.colors.primary }}
											title="Primary"
										/>
										<div
											className="h-[32px] w-[32px] rounded-[4px] border border-[#DDE2E5]"
											style={{ backgroundColor: activeTheme.config.colors.gray }}
											title="Gray"
										/>
										<div
											className="h-[32px] w-[32px] rounded-[4px] border border-[#DDE2E5]"
											style={{ backgroundColor: activeTheme.config.colors.success }}
											title="Success"
										/>
										<div
											className="h-[32px] w-[32px] rounded-[4px] border border-[#DDE2E5]"
											style={{ backgroundColor: activeTheme.config.colors.warning }}
											title="Warning"
										/>
									</>
								)}
							</div>
						</div>

						<div>
							<span className="font-lato text-[14px] text-[#6C747D]">
								Font Family
							</span>
							<p className="mt-[2px] font-lato text-[14px] font-medium text-[#212429]">
								{activeTheme.config?.typography?.font_family || 'Default'}
							</p>
						</div>
					</>
				) : (
					<div className="py-[20px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">
							No themes configured
						</p>
						<p className="mt-[4px] font-lato text-[12px] text-[#6C747D]">
							Create your first theme to customize the app appearance
						</p>
					</div>
				)}
			</div>

			{/* Card Footer */}
			<Link
				to={`/platform/apps/${appId}/app-settings/app-configuration/#themes`}
				className="mt-auto flex items-center justify-between rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] transition-colors hover:bg-[#F0F3F4]"
			>
				<span className="font-lato text-[14px] font-medium text-[#212429]">
					Manage Themes
				</span>
				<ArrowRightIcon className="h-[16px] w-[16px] text-[#6C747D]" />
			</Link>
		</div>
	);
}