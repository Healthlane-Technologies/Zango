/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ['./src/**/*.{js,jsx,ts,tsx}'],
	theme: {
		extend: {
			fontFamily: {
				lato: ['"Lato"', 'sans-serif'],
				'open-sans': ['"Open Sans"', 'sans-serif'],
				'source-sans-pro': ['"Source Sans Pro"', 'sans-serif'],
			},
			fontSize: {
				'portal-sm': [
					'14px',
					{
						lineHeight: '19px',
					},
				],
				'portal-xl': [
					'20px',
					{
						lineHeight: '27px',
					},
				],
				'card-sm': [
					'14px',
					{
						lineHeight: '24px',
						letterSpacing: '1px',
					},
				],
				'card-base': [
					'16px',
					{
						lineHeight: '20px',
					},
				],
				'card-label-sm': [
					'14px',
					{
						lineHeight: '20px',
					},
				],
				'form-xs': [
					'12px',
					{
						lineHeight: '16px',
						letterSpacing: '0.2px',
					},
				],
				'profile-menu-base': [
					'16px',
					{
						lineHeight: '21px',
					},
				],
				'appbar-xxs': [
					'8px',
					{
						lineHeight: '11px',
					},
				],
			},

			flexGrow: {
				2: 2,
				3: 3,
			},
			colors: {
				primary: '#5048ED',
				secondary: '#E1D6AE',
				error: '#FBE0DD',
				'primary-light': '#bcb9f8',
				'danger-red': '#AA2113',
				'dark-gray': '#696969',
				'medium-gray': '#9A9A9A',
				'light-gray': '#D4D4D4',
				'off-white': '#f7f7f7',
				'on-hold': '#FFEFD4',
				'error-text': '#55100A',
			},
			spacing: {
				0.5: '0.125',
				30: '7.5rem',
				31: '7.75rem',
				7: '1.75rem',
				21: '5.25rem',
				'7/2': '0.875rem',
				13: '3.25rem',
			},
			boxShadow: {
				dropdown: '0px 0px 12px rgba(0, 0, 0, 0.16)',
				navbar: '0px 2px 8px rgba(84, 84, 84, 0.04)',
				top: '0px -8px 20px rgba(40, 58, 70, 0.08);',
				eachApp: '0px 4px 20px 0px rgba(0, 0, 0, 0.12)',
				appSort: '0px 4px 24px 0px rgba(0, 0, 0, 0.16)',
				notification: '0px 4px 24px 0px rgba(0, 0, 0, 0.16)',
				'portal-card': '0px 0px 12px rgba(0, 0, 0, 0.08)',
				'primary-card': '0px 0px 12px rgba(0, 0, 0, 0.08)',
				'infusion-card': '0px 0px 12px rgba(0, 0, 0, 0.08)',
				'primary-menu': ' 0px 0px 12px rgba(0, 0, 0, 0.12)',
				'table-row': '0px 2px 8px 0px rgba(0, 0, 0, 0.16)',
				'table-menu': '0px 4px 24px 0px rgba(0, 0, 0, 0.16)',
				'form-select': '0px 4px 24px 0px rgba(0, 0, 0, 0.16)',
			},
			height: {
				screen: 'var(--app-height)',
			},
			animation: {
				enter: 'enter 200ms ease-out',
				leave: 'leave 150ms ease-in forwards',
				'slide-in': 'slide-in 1.2s cubic-bezier(.41,.73,.51,1.02)',
			},
			keyframes: {
				enter: {
					'0%': { transform: 'scale(0.9)', opacity: 0 },
					'100%': { transform: 'scale(1)', opacity: 1 },
				},
				leave: {
					'0%': { transform: 'scale(1)', opacity: 1 },
					'100%': { transform: 'scale(0.9)', opacity: 0 },
				},
				'slide-in': {
					'0%': { transform: 'translateY(-100%)' },
					'100%': { transform: 'translateY(0)' },
				},
			},
		},
	},
	plugins: [],
};
