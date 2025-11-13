import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddThemeIcon } from '../../../../assets/images/svg/add-theme-icon.svg';
import useApi from '../../../../hooks/useApi';
import { transformToFormData } from '../../../../utils/form';
import { setAppConfigurationData } from '../../../appConfiguration/slice';
import {
	openIsAddThemeModalOpen,
	openIsEditThemeModalOpen,
	selectAppThemeConfigurationData,
	selectRerenderPage,
	setAppThemeConfigurationData,
	toggleRerenderPage,
} from '../../slice';
import AddThemeModal from '../Modals/AddThemeModal';
import EditThemeModal from '../Modals/EditThemeModal';

const ModernThemeConfiguration = () => {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	const rerenderPage = useSelector(selectRerenderPage);
	const appThemeConfigurationData = useSelector(selectAppThemeConfigurationData);
	

	function updateAppThemeConfigurationData(value) {
		dispatch(setAppThemeConfigurationData(value));
	}

	function updateAppConfigurationData(value) {
		dispatch(setAppConfigurationData(value));
	}

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppConfigurationData(response);
			}
		};

		makeApiCall();
	}, []);

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/themes/?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppThemeConfigurationData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	if (!appThemeConfigurationData) {
		return (
			<div className="flex items-center justify-center h-64">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#5048ED] mx-auto mb-4"></div>
					<p className="text-[#6B7280]">Loading themes...</p>
				</div>
			</div>
		);
	}

	const themes = appThemeConfigurationData?.themes || [];
	const activeTheme = themes.find(theme => theme.is_active);

	const handleAddTheme = () => {
		dispatch(openIsAddThemeModalOpen());
	};

	const handleEditTheme = (theme) => {
		dispatch(openIsEditThemeModalOpen(theme));
	};

	const handleActivateTheme = async (theme) => {
		let tempValues = {
			is_active: true,
		};

		let dynamicFormData = transformToFormData(tempValues);

		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/themes/${theme.id}/`,
			type: 'PUT',
			loader: true,
			payload: dynamicFormData,
		});
		
		if (success && response) {
			dispatch(toggleRerenderPage());
		}
	};

	const handleDeleteTheme = async (themeId) => {
		if (window.confirm('Are you sure you want to delete this theme?')) {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/themes/${themeId}/`,
				type: 'DELETE',
				loader: true,
			});
			if (success) {
				dispatch(toggleRerenderPage());
			}
		}
	};

	// Color preview component
	const ColorPreview = ({ color, label }) => (
		<div className="flex items-center gap-[8px]">
			<div 
				className="w-[24px] h-[24px] rounded-[6px] border border-[#E5E7EB]" 
				style={{ backgroundColor: color }}
			/>
			<span className="text-[12px] text-[#6B7280]">{label}</span>
		</div>
	);

	// Theme card for grid view
	const ThemeCard = ({ theme }) => {
		// Get colors from theme config, handling both nested and flat structures
		// Note: API returns 'color' (singular) not 'colors' (plural) for default theme
		const colors = theme.config?.colors || theme.config?.color || theme.colors || {};
		const hasColors = Object.keys(colors).length > 0;

		return (
			<div className={`relative bg-white rounded-[12px] border p-[20px] transition-all hover:shadow-md ${
				theme.is_active ? 'border-[#5048ED] shadow-md ring-2 ring-[#5048ED]/20' : 'border-[#E5E7EB]'
			}`}>
				{/* Active Badge */}
				{theme.is_active && (
					<div className="absolute -top-[12px] left-1/2 transform -translate-x-1/2">
						<div className="relative">
							<div className="absolute inset-0 bg-[#5048ED] rounded-full animate-pulse"></div>
							<div className="relative bg-[#5048ED] text-white px-[16px] py-[4px] rounded-full shadow-lg">
								<div className="flex items-center gap-[6px]">
									<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
										<path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
									<span className="text-[11px] font-semibold uppercase tracking-wider">Active</span>
								</div>
							</div>
						</div>
					</div>
				)}

				{/* Header */}
				<div className="flex items-start justify-between mb-[16px]">
					<div>
						<h4 className="text-[16px] font-semibold text-[#111827] mb-[4px]">{theme.name}</h4>
					</div>
					<div className="flex items-center gap-[4px]">
						<button
							onClick={() => handleEditTheme(theme)}
							className="p-[6px] text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6] rounded-[4px] transition-colors"
							title="Edit theme"
						>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M11.334 2C11.722 1.612 12.278 1.612 12.666 2L14 3.334C14.388 3.722 14.388 4.278 14 4.666L5 13.666L2 14.666L3 11.666L11.334 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</button>
						{!theme.is_active && (
							<button
								onClick={() => handleDeleteTheme(theme.id)}
								className="p-[6px] text-[#6B7280] hover:text-[#EF4444] hover:bg-[#FEE2E2] rounded-[4px] transition-colors"
								title="Delete theme"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M2 4H14M5.333 4V2.667C5.333 2.298 5.632 2 6 2H10C10.368 2 10.667 2.298 10.667 2.667V4M6.667 7.333V10.667M9.333 7.333V10.667M3.333 4L4 12.667C4 13.403 4.597 14 5.333 14H10.667C11.403 14 12 13.403 12 12.667L12.667 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							</button>
						)}
					</div>
				</div>

				{/* Colors */}
				<div className="space-y-[12px] mb-[16px]">
					<div className="grid grid-cols-2 gap-[8px]">
						{hasColors ? (
							<>
								<ColorPreview color={colors.primary || '#5048ED'} label="Primary" />
								<ColorPreview color={colors.secondary || '#6B7280'} label="Secondary" />
								<ColorPreview color={colors.background || '#FFFFFF'} label="Background" />
								<ColorPreview color={colors.gray || '#9CA3AF'} label="Gray" />
								<ColorPreview color={colors.success || '#10B981'} label="Success" />
								<ColorPreview color={colors.warning || '#F59E0B'} label="Warning" />
								<ColorPreview color={colors.error || '#EF4444'} label="Error" />
								<ColorPreview color={colors.info || '#3B82F6'} label="Info" />
							</>
						) : (
							<div className="col-span-2 text-[12px] text-[#9CA3AF] text-center py-2">
								No color configuration available
							</div>
						)}
					</div>
				</div>

				{/* Typography */}
				<div className="pt-[12px] border-t border-[#F3F4F6] space-y-[8px]">
					<div>
						<p className="text-[11px] text-[#6B7280] mb-[2px]">Font Family</p>
						<p className="text-[12px] text-[#111827] truncate font-medium">{theme.config?.typography?.font_family?.split(',')[0] || 'Default'}</p>
					</div>
					<div className="flex gap-[12px]">
						<div>
							<p className="text-[11px] text-[#6B7280] mb-[2px]">Font Size</p>
							<p className="text-[12px] text-[#111827]">{theme.config?.typography?.font_size_base || '14px'}</p>
						</div>
						<div>
							<p className="text-[11px] text-[#6B7280] mb-[2px]">Line Height</p>
							<p className="text-[12px] text-[#111827]">{theme.config?.typography?.line_height || '1.5'}</p>
						</div>
					</div>
				</div>

				{/* Actions */}
				{!theme.is_active && (
					<button
						onClick={() => handleActivateTheme(theme)}
						className="mt-[16px] w-full py-[8px] bg-[#F3F4F6] text-[#111827] rounded-[6px] text-[13px] font-medium hover:bg-[#E5E7EB] transition-colors"
					>
						Set as Active
					</button>
				)}
			</div>
		);
	};


	return (
		<div className="max-w-[1400px] mx-auto">
			{/* Header */}
			<div className="flex items-center justify-between mb-[32px]">
				<div>
					<h2 className="text-[24px] font-semibold text-[#111827] mb-[4px]">Theme Configuration</h2>
					<p className="text-[14px] text-[#6B7280]">Customize the visual appearance of your application</p>
				</div>
				{/* Add Theme Button */}
				<button
						onClick={handleAddTheme}
						className="flex items-center gap-[8px] px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
					>
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
							<path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
						</svg>
						<span className="font-medium text-[14px]">Add Theme</span>
					</button>
			</div>


			{/* Themes List/Grid */}
			{themes.length === 0 ? (
				<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[48px] text-center">
					<div className="w-[80px] h-[80px] bg-[#F3F4F6] rounded-full flex items-center justify-center mx-auto mb-[24px]">
						<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
							<path d="M20 5L23.09 12.26L31.18 13.27L25.09 18.94L26.18 27.02L20 23.27L13.82 27.02L14.91 18.94L8.82 13.27L16.91 12.26L20 5Z" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					</div>
					<h3 className="text-[20px] font-semibold text-[#111827] mb-[8px]">No Themes Created</h3>
					<p className="text-[14px] text-[#6B7280] mb-[24px]">Create your first theme to customize your app's appearance</p>
					<button
						onClick={handleAddTheme}
						className="inline-flex items-center gap-[8px] px-[20px] py-[10px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
					>
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M10 5V15M5 10H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
						</svg>
						<span className="font-medium">Create First Theme</span>
					</button>
				</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[20px]">
					{themes.map((theme) => (
						<ThemeCard key={theme.id} theme={theme} />
					))}
				</div>
			)}

			{/* Modals */}
			<AddThemeModal />
			<EditThemeModal />
		</div>
	);
};

export default ModernThemeConfiguration;