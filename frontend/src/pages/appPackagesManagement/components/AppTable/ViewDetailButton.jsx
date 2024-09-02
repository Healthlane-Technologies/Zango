import { useState, useEffect } from "react";
import useApi from "../../../../hooks/useApi";
import { ReactComponent as DetailEyeIcon } from '../../../../assets/images/svg/detail-eye-icon.svg';
import { openIsConfigurePackageModalOpen } from "../../slice";

const ViewDetailButton = ({info,dispatch})=>{
	const [disable,setDisable] = useState(true)
	const triggerApi = useApi()
	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/:appId/packages/?action=config_url&package_name=${info.row.original.name}`,
				type: 'GET',
				loader: true,
			});
			setDisable(success)
		};
		makeApiCall()
	}, [])

	return <div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
		<button
				className="flex items-center gap-[12px] disabled:opacity-25"
				onClick={() => {
					dispatch(openIsConfigurePackageModalOpen(info.row.original));
				}}
				disabled={!disable}
			>
				<span
					className={`w-fit min-w-max rounded-[15px] text-center font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px] text-[#5048ED]`}
				>
					View Details
				</span>
				<DetailEyeIcon />
			</button>
		</div>
	
}

export default ViewDetailButton;