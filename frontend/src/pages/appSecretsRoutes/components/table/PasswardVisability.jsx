import React, { useState } from 'react';
import useApi from '../../../../hooks/useApi';
import { useParams } from 'react-router-dom';
import { ReactComponent as AsteriskIcon } from '../../../../assets/images/svg/asterisk-icon.svg';
import { ReactComponent as EyeIcon } from '../../../../assets/images/svg/eye.svg';
import { ReactComponent as EyeOffIcon } from '../../../../assets/images/svg/eye-off.svg';

const PasswardVisability = ({ info }) => {
	let { appId } = useParams();
	const triggerApi = useApi();
	const [secretValue, setSecretValue] = React.useState('');
	const [isVisible, setIsVisible] = React.useState(false);
	const [isLoading, setIsLoading] = useState(false)

	const items = Array.from({ length: 8 }, (_, i) => i);

	const handleViewSecret = async () => {
		if (isVisible) {
			setSecretValue('');
			setIsVisible(false);
			return;
		}
		setIsLoading(true)

		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/secrets/?secret_id=${info.row.original.id}&action=get_secret_value`,
			type: 'GET',
			loader: false,
		});

		if (success) {
			setSecretValue(response.secret_value);
			setIsVisible(true);
		}
		setIsLoading(false)
	};

	return (
		<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
			<span className="flex cursor-pointer items-center gap-2 text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#6C747D]">
				{secretValue ? (
					<span className="font-lato text-[14px] font-normal text-[#6C747D]">
						{secretValue}
					</span>
				) : (
					<span className="flex">
						{items.map((item) => (
							<AsteriskIcon key={item} />
						))}
					</span>
				)}
				<span
					onClick={!isLoading ? handleViewSecret : undefined}
					className={`cursor-pointer text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px] ${isLoading ? 'opacity-50 cursor-not-allowed' : 'text-[#6C747D]'}`}
				>
					{isVisible ? <EyeOffIcon /> : <EyeIcon />}
				</span>
				<span>
					{isLoading && (
						<div className="h-5 w-5 animate-spin rounded-full border-b-2 border-primary"></div>
					)}
				</span>
			</span>
		</div>
	);
};

export default PasswardVisability;
