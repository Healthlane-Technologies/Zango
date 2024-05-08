import { useState } from 'react';

const ListRoleCell = ({ data }) => {
	const [show, setShow] = useState(false);

	const handleToggle = () => {
		setShow((prev) => !prev);
	};

	return (
		<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
			{data.map((eachApp, index) => {
				return (
					<div key={eachApp?.id} className="flex items-center gap-[12px]">
						{show ? (
							<span
								key={eachApp?.id}
								className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]"
							>
								{eachApp?.name}
							</span>
						) : index < 3 ? (
							<span
								key={eachApp?.id}
								className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]"
							>
								{eachApp?.name}
							</span>
						) : null}
						{data.length === index + 1 && index > 2 ? (
							<button
								type="button"
								onClick={handleToggle}
								className="min-w-max text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#5048ED]"
							>
								{show ? null : '+'}
								{show ? null : data.length - 3} {show ? 'less' : 'more'}
							</button>
						) : null}
					</div>
				);
			})}
		</div>
	);
};

export default ListRoleCell;
