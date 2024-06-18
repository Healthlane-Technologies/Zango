import { useState } from 'react';

const ListGeneralCell = ({ data, info }) => {
	let minShow = 8;
	const [show, setShow] = useState(false);

	const handleToggle = () => {
		setShow((prev) => !prev);
	};

	return (
		<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
			<table class="table-auto">
				<thead>
					<tr>
						<th></th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{Object.entries(data).map((eachChange, index, dataArray) => {
						if (!Array.isArray(eachChange[1])) {
							return (
								<>
									<tr>
										<td className="min-w-[150px] max-w-[150px] pr-[24px]">
											<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
												field
											</span>
										</td>
										<td className="min-w-[500px] max-w-[500px] pr-[10px]">
											<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
												:{''}
												<span>{eachChange[0].split('_').join(' ')}</span>
											</span>
										</td>
									</tr>
									<tr>
										<td className="min-w-[150px] max-w-[150px] pr-[24px]">
											<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
												type
											</span>
										</td>
										<td className="min-w-[500px] max-w-[500px] pr-[10px]">
											<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
												:{''}
												<span>{eachChange[1]?.type}</span>
											</span>
										</td>
									</tr>
									<tr>
										<td className="min-w-[150px] max-w-[150px] pr-[24px]">
											<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
												objects
											</span>
										</td>
										<td className="min-w-[500px] max-w-[500px] pr-[10px]">
											<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
												:{''}
												<span>{eachChange[1]?.objects.join(', ')}</span>
											</span>
										</td>
									</tr>
									<tr>
										<td className="min-w-[150px] max-w-[150px] pr-[24px]">
											<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
												operation
											</span>
										</td>
										<td className="min-w-[500px] max-w-[500px] pr-[10px]">
											<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
												:{''}
												<span>{eachChange[1]?.operation}</span>
											</span>
										</td>
									</tr>
								</>
							);
						}

						return (
							<>
								{show ? (
									<tr>
										<td className="min-w-[150px] max-w-[150px] pr-[24px] align-top">
											<span className="text-balance text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
												{eachChange[0].split('_').join(' ')}
											</span>
										</td>
										<td className="min-w-[500px] max-w-[500px] pr-[10px] align-top">
											<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
												:{''}
												{eachChange[1].map(
													(changesValue, index, arrayContext) => {
														if (
															index === 0 &&
															info.row.original?.action === 'Create'
														) {
															return <></>;
														}
														return (
															<span
																className={`text-balance text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] ${
																	arrayContext?.length - 1 !== index
																		? 'min-w-[225px] max-w-[220px] text-balance break-all text-[#A3ABB1]'
																		: 'break-all'
																}`}
															>
																{!changesValue ? '<empty>' : changesValue}
																{arrayContext?.length - 1 !== index
																	? ' ->'
																	: ''}
															</span>
														);
													}
												)}
											</span>
										</td>
									</tr>
								) : index < minShow ? (
									<tr>
										<td className="min-w-[150px] max-w-[150px] pr-[24px] align-top">
											<span className="text-balance text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
												{eachChange[0].split('_').join(' ')}
											</span>
										</td>
										<td className="min-w-[500px] max-w-[500px] pr-[10px] align-top">
											<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
												:{''}
												{eachChange[1].map(
													(changesValue, index, arrayContext) => {
														if (
															index === 0 &&
															info.row.original?.action === 'Create'
														) {
															return <></>;
														}
														return (
															<>
																<span
																	className={`text-balance  text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] ${
																		arrayContext?.length - 1 !== index
																			? 'min-w-[225px] max-w-[220px] text-balance break-all text-[#A3ABB1]'
																			: 'break-all'
																	}`}
																>
																	{!changesValue ? '<empty>' : changesValue}
																</span>
																<span className="whitespace-nowrap text-[#A3ABB1]">
																	{arrayContext?.length - 1 !== index
																		? ' ->'
																		: ''}
																</span>
															</>
														);
													}
												)}
											</span>
										</td>
									</tr>
								) : null}

								{dataArray?.length === index + 1 && index > minShow - 1 ? (
									<button
										type="button"
										onClick={handleToggle}
										className="min-w-max text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#5048ED]"
									>
										{show ? null : '+'}
										{show ? null : dataArray?.length - minShow}{' '}
										{show ? 'less' : 'more'}
									</button>
								) : null}
							</>
						);
					})}
				</tbody>
			</table>
		</div>
	);
};

export default ListGeneralCell;
