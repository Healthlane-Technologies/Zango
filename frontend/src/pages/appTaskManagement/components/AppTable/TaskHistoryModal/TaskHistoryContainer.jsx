import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { selectAppTaskHistoryData } from '../../../slice';
import moment from 'moment';

function TaskHistoryContainer() {
	const [visibleCodeIndex, setVisibleCodeIndex] = useState(null);

	const TaskHistoryData = useSelector(selectAppTaskHistoryData);

	const handleToggleCode = (index) => {
		setVisibleCodeIndex(visibleCodeIndex === index ? null : index);
	};

	return (
		<div className="overflow-y-auto">
			<div className="mb-3 text-right text-[12px] text-[#495057]">
				* All timestamps shown here are in UTC
			</div>
			{TaskHistoryData?.task?.run_history.map((eachHistory, index) => (
				<div key={index} className="mb-2 w-full rounded-[6px] border-2 p-4">
					<p className="py-1 font-open-sans text-base font-semibold text-[#495057]">
						Start Date & Time:{' '}
						<span className="text-sm font-normal">
							{eachHistory?.date_created}
						</span>
					</p>
					<p className="py-1 font-open-sans text-base font-semibold text-[#495057]">
						End Date & Time:{' '}
						<span className="text-sm font-normal">
							{eachHistory?.date_done}
						</span>
					</p>
					<p className="py-1 font-open-sans text-base font-semibold text-[#495057]">
						Result:{' '}
						<span className="text-sm font-normal">{eachHistory?.result}</span>
					</p>
					{eachHistory?.traceback !== null && (
						<button
							onClick={() => handleToggleCode(index)}
							className="font-open-sans text-sm font-semibold text-[#5048ED]"
						>
							{visibleCodeIndex === index
								? 'Hide Traceback '
								: 'View Traceback'}
						</button>
					)}

					{visibleCodeIndex === index && (
						<p className="mt-4 overflow-x-scroll rounded-md bg-gray-100 p-2 font-mono text-sm">
							{eachHistory?.traceback}
						</p>
					)}
				</div>
			))}
		</div>
	);
}

export default TaskHistoryContainer;
