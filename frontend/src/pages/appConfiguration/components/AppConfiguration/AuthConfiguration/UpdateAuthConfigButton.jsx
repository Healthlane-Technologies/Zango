import React from "react";
import { useNavigate, useLocation } from "react-router-dom";

const UpdateAuthConfigButton = () => {
	const navigate = useNavigate();
	const location = useLocation();

	const handleUpdateAuthConfig = (e) => {
		e.preventDefault();
		e.stopPropagation();
		console.log("Current location:", location.pathname);
		console.log("Navigating to: ./configure");
		
		// Check if we're on the auth page specifically
		if (location.pathname.includes('/auth')) {
			navigate("./configure");
		} else {
			navigate("./auth/configure");
		}
	};

	return (
		<button
			type="button"
			className="flex h-[40px] w-fit items-center justify-center gap-[8px] rounded-[8px] border border-[#5048ED] bg-[#5048ED] px-[16px] py-[8px] text-[14px] font-medium text-white shadow-sm transition-colors hover:bg-[#3d38c7] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:ring-offset-2"
			onClick={handleUpdateAuthConfig}
		>
			<svg
				width="16"
				height="16"
				viewBox="0 0 16 16"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					d="M11.013 1.427A1.75 1.75 0 0 1 13.427 2.987L12.22 4.193a.25.25 0 0 1-.427-.177V3.75A.25.25 0 0 1 12.043 3.5h.25a.25.25 0 0 1 .177.073l.543.543ZM9.22 4.22a.75.75 0 0 1 1.06 0l1.5 1.5a.75.75 0 0 1 0 1.06l-1.5 1.5a.75.75 0 0 1-1.06-1.06l.22-.22H3.75a.75.75 0 0 1 0-1.5h5.69l-.22-.22a.75.75 0 0 1 0-1.06Z"
					fill="currentColor"
				/>
			</svg>
			Configure Authentication
		</button>
	);
};

export default UpdateAuthConfigButton;