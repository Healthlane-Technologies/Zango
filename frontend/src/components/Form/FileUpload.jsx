import React from 'react';

import { ReactComponent as UploadIcon } from '../../assets/images/svg/upload-icon.svg';
import { ReactComponent as UploadCloseIcon } from '../../assets/images/svg/upload-close-icon.svg';
import { useState } from 'react';

export default function FileUpload({ formik, label, id, fileValue }) {
	const [previewUrl, setPreviewUrl] = useState();

	return (
		<div data-cy="file_upload" className="flex flex-col gap-[4px]">
			<div className="flex w-full flex-col gap-4">
				<div className="flex w-full flex-col gap-1">
					<label className="font-lato text-form-xs font-semibold text-[#A3ABB1]">
						Upload {label}
					</label>
					<label
						htmlFor={id}
						className={`flex w-full items-center justify-between rounded-[6px] border border border-[#D5D5D5] border-[#DDE2E5] px-[16px] py-[14px] font-lato hover:outline-0 focus:outline-0 ${
							formik.values[id]?.name
								? 'text-[#000000]'
								: 'border-dashed text-[#9A9A9A]'
						}`}
					>
						<div className="flex w-[calc(100%_-_16px)] items-center gap-[12px]">
							{formik.values[id]?.name ? (
								<a href={previewUrl} target="_blank" rel="noreferrer">
									<img
										className="h-[32px] min-h-[32px] w-[32px] min-w-[32px]"
										src={previewUrl}
										alt={`${id}_preview`}
									/>
								</a>
							) : null}
							<span className="overflow-hidden text-ellipsis">
								{formik.values[id]?.name
									? formik.values[id]?.name
									: `Click to Upload ${label}`}
							</span>
						</div>
						{formik.values[id]?.name ? (
							<button
								type="button"
								onClick={(event) => {
									event.preventDefault();
									formik.setFieldValue(id, '');
								}}
							>
								<UploadCloseIcon />
							</button>
						) : (
							<UploadIcon />
						)}
					</label>
					{formik.errors[id] ? (
						<div className="font-lato text-form-xs text-[#cc3300]">
							{formik.errors[id]}
						</div>
					) : null}
					<input
						type="file"
						multiple={false}
						id={id}
						name={id}
						className="hidden h-0 w-0"
						onChange={(e) => {
							formik.setFieldValue(id, e.target.files?.[0]);
							setPreviewUrl(URL.createObjectURL(e.target.files[0]));
							e.target.value = '';
						}}
					/>
				</div>
			</div>
			{fileValue && !formik.values.logo ? (
				<a href={fileValue} alt="" target={'_blank'} rel="noreferrer">
					<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
						File Link
					</span>
				</a>
			) : null}
		</div>
	);
}
