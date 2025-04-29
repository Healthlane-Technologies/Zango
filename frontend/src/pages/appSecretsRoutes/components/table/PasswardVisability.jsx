import React from 'react';
import useApi from '../../../../hooks/useApi';
import { useParams } from 'react-router-dom';
import { ReactComponent as AsteriskIcon } from '../../../../assets/images/svg/asterisk-icon.svg';
import { ReactComponent as EyeIcon } from '../../../../assets/images/svg/eye.svg';

const PasswardVisability = ({ info }) => {
	let { appId } = useParams();
	const triggerApi = useApi();
	const [secretValue, setSecretValue] = React.useState('');
	const handleViewSecret = async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/secrets/?secret_id=${info.row.original.id}&action=get_secret_value`,
			type: 'GET',
			loader: true,
		});

		if (success) {
			console.log(response);
			setSecretValue(response.secret_value);
		}
	};

	return (
		<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
			<span
				onClick={handleViewSecret}
				className="flex cursor-pointer items-center gap-2 text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px] text-[#6C747D]"
			>
				{secretValue ? (
					<span className="font-lato text-[14px] font-normal text-[#6C747D]">
						{secretValue}
					</span>
				) : (
					<span className="flex">
						<AsteriskIcon />
						<AsteriskIcon />
						<AsteriskIcon />
						<AsteriskIcon />
						<AsteriskIcon />
						<AsteriskIcon />
						<AsteriskIcon />
						<AsteriskIcon />
					</span>
				)}
				<span
					onClick={handleViewSecret}
					className="cursor-pointer text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px] text-[#6C747D]"
				>
					<EyeIcon />
				</span>
			</span>
		</div>
	);
};

export default PasswardVisability;
