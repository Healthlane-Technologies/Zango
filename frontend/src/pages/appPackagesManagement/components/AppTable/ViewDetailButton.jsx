import { useState, useEffect } from "react";
import { ReactComponent as DetailEyeIcon } from '../../../../assets/images/svg/detail-eye-icon.svg';
import { openIsConfigurePackageModalOpen } from "../../slice";

const ViewDetailButton = ({info,dispatch})=>{
	let configUrl = info.row.original.config_url
	const [disable,setDisable] = useState(true)
	useEffect(()=>{
		setDisable(configUrl!==null)
	},[])

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