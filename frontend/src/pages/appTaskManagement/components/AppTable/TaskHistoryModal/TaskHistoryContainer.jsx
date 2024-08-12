import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { selectAppTaskHistoryData } from '../../../slice';
import moment from 'moment';

function TaskHistoryContainer() {
	const [visibleCodeIndex, setVisibleCodeIndex] = useState(null); // State to track the visible code

	const TaskHistoryData = useSelector(selectAppTaskHistoryData);

	const handleToggleCode = (index) => {
		// Toggle the visibility of the code for the selected index
		setVisibleCodeIndex(visibleCodeIndex === index ? null : index);
	};

	return (
		<div className="overflow-y-auto">
			{TaskHistoryData?.task?.run_history.map((eachHistory, index) => (
				<div key={index} className="border-2 rounded-[6px] mb-2 p-4 w-full">
					<p className="font-open-sans text-base font-semibold text-[#495057] py-1">
						Start Time: <span className="font-normal">{moment(eachHistory?.date_created).format('DD MMM YYYY')}</span>
					</p>
					<p className="font-open-sans text-base font-semibold text-[#495057] py-1">
						End Time: <span className="font-normal">{moment(eachHistory?.date_done).format('DD MMM YYYY')}</span>
					</p>
					<p className="font-open-sans text-base font-semibold text-[#495057] py-1">
						Status: <span className="font-normal">COMPLETED</span>
					</p>
					<button
						onClick={() => handleToggleCode(index)}
						className="font-open-sans text-sm font-semibold text-[#5048ED]"
					>
						{visibleCodeIndex === index ? 'Hide Code' : 'View Code'}
					</button>

					{visibleCodeIndex === index && (
						<p className="mt-4 bg-gray-100 p-2 rounded-md font-mono text-sm">
							{eachHistory?.traceback} 
						</p>
					)}
				</div>
			))}
		</div>
	);
}

export default TaskHistoryContainer;
