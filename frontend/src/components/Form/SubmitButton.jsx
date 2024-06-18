function SubmitButton({
	label,
	formik,
	allowDisabled = true,
	theme = 'normal',
}) {
	return (
		<button
			type="submit"
			className={`flex w-full items-center justify-center rounded-[4px] ${
				{
					normal: 'bg-primary',
					danger: 'bg-danger-red',
					success: 'bg-[#229470]',
				}[theme]
			} px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]`}
			disabled={allowDisabled ? !(formik.isValid && formik.dirty) : false}
		>
			<span>{label}</span>
		</button>
	);
}

export default SubmitButton;
