function SubmitButton({
	label,
	formik,
	allowDisabled = true,
	theme = 'normal',
}) {
	return (
		<button
			type="submit"
			className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
				{
					normal: 'bg-primary hover:bg-primary/90 focus:ring-primary',
					danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-600',
					success: 'bg-green-600 hover:bg-green-700 focus:ring-green-600',
				}[theme]
			}`}
			disabled={allowDisabled ? !(formik.isValid && formik.dirty) : false}
		>
			{label}
		</button>
	);
}

export default SubmitButton;
