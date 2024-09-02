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
// export const getCsrfToken = () => {
    
// };
export const getCookie = () => {
	// let csrfToken = '';
	// let csrf_token = getCsrfToken()
	// console.log('csrf',csrf_token)
	// /*eslint-disable */
	// if (csrf_token !== 'undefined') {
	// 	csrfToken = csrf_token;
	// }

	// return csrfToken;
	const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i];
        while (cookie.charAt(0) === ' ') {
            cookie = cookie.substring(1);
        }
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return null; // or handle token not found scenario
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
export const detectBrowser = () => {
    const userAgent = window.navigator.userAgent;
    const vendor = window.navigator.vendor;

    if (userAgent.indexOf("Chrome") !== -1) {
      return "chrome";
    } else if (userAgent.indexOf("Safari") !== -1) {
      return "safari";
    } else if (userAgent.indexOf("Firefox") !== -1) {
      return "firefox";
    } else if (userAgent.indexOf("Edge") !== -1) {
      return "edge";
    } else {
      return "Unknown";
    }
  };