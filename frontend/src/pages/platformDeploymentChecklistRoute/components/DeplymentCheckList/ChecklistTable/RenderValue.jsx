const RenderValue = ({ value }) => {
	if (typeof value === 'boolean') {
		return (
			<span>
				{value ? (
					<div className="flex gap-2 items-center">
						<span className="h-2 w-2 rounded-full bg-[#2CBE90]"></span>
						Enabled
					</div>
				) : (
					<div className="flex gap-2 items-center">
						<span className="h-2 w-2 rounded-full bg-[#D52918]"></span>
						Disabled
					</div>
				)}
			</span>
		);
	}

	if (typeof value === 'string' || typeof value === 'number') {
		return <span>{value}</span>;
	}

	if (Array.isArray(value)) {
		return <span>{value.join(', ')}</span>;
	}

	if (typeof value === 'object' && value !== null) {
		return (
			<ul className="ml-4 list-disc">
				{Object.entries(value).map(([key, val]) => (
					<li key={key}>
						<strong>{key}:</strong> {val.toString()}
					</li>
				))}
			</ul>
		);
	}

	return <span>Unsupported Data Type</span>;
};

export default RenderValue;