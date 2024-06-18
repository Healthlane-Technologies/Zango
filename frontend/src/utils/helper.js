/**
 * Check if app started in mock mode
 * @returns boolean
 */
export function isMockApi() {
	return process.env.REACT_APP_MSW_MOCK_API === 'true';
}

/**
 * Fetch CSRF token which is passed in html file by Django code
 * @returns CSRF Token
 */
export const getCookie = () => {
	let csrfToken = '';

	/*eslint-disable */
	if (csrf_token !== 'undefined') {
		csrfToken = csrf_token;
	}

	return csrfToken;
};

/**
 * Fetch Platform version which is passed in html file by Django code
 * @returns Platform version
 */
export const getPlatformVersion = () => {
	let platformVersion = '';

	/*eslint-disable */
	if (platform_version !== 'undefined') {
		platformVersion = platform_version;
	}

	return platformVersion;
};
