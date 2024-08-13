import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { selectAppTaskHistoryData } from '../../../slice';
import moment from 'moment';
import { Editor } from '@monaco-editor/react';

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
				<div key={index} className="mb-2 w-full rounded-[6px] border-2 p-4">
					<p className="py-1 font-open-sans text-base font-semibold text-[#495057]">
						Start Time:{' '}
						<span className="font-normal">
							{moment(eachHistory?.date_created).format('DD MMM YYYY')}
						</span>
					</p>
					<p className="py-1 font-open-sans text-base font-semibold text-[#495057]">
						End Time:{' '}
						<span className="font-normal">
							{moment(eachHistory?.date_done).format('DD MMM YYYY')}
						</span>
					</p>
					<p className="py-1 font-open-sans text-base font-semibold text-[#495057]">
						Status: <span className="font-normal">{eachHistory?.result}</span>
					</p>
					<button
						onClick={() => handleToggleCode(index)}
						className="font-open-sans text-sm font-semibold text-[#5048ED]"
					>
						{visibleCodeIndex === index ? 'Hide Code' : 'View Code'}
					</button>

					{visibleCodeIndex === index && (
						<>
							<div className="flex flex-col gap-2">
								{/* <div>{info.row.original?.docstring}</div> */}
								<Editor
									height="250px"
									width="100%"
									theme="vs-dark"
									defaultLanguage="python"
									defaultValue={eachHistory?.traceback}
								/>
							</div>

							<p className="mt-4 rounded-md bg-gray-100 p-2 font-mono text-sm"></p>
						</>
					)}
				</div>
			))}
		</div>
	);
}

export default TaskHistoryContainer;
