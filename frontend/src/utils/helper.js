/**
 * Check if app started in mock mode
 * @returns boolean
 */
export function isMockApi() {
	return process.env.REACT_APP_MSW_MOCK_API === 'true';
}

function getPageCookie(name) {
	const cookies = document.cookie.split('; ');
	for (const cookie of cookies) {
		const [key, value] = cookie.split('=');
		if (key === name) {
			return decodeURIComponent(value);
		}
	}
	return null;
}

/**
 * Fetch CSRF token which is passed in html file by Django code
 * @returns CSRF Token
 */
export const getCookie = () => {
	let csrfToken = '';

	/*eslint-disable */
	if (csrf_token !== 'undefined') {
		csrfToken = csrf_token || getPageCookie('csrftoken');
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

export function getRepoName(githubUrl) {
    const regex = /github\.com\/([^/]+\/[^/]+)/;
    const match = githubUrl.match(regex);
    return match ? match[1] : null;
}