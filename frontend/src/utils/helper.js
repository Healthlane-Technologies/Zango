export function isMockApi() {
	return process.env.REACT_APP_MSW_MOCK_API === 'true';
}

export const getCookie = () => {
	let csrfToken = '';

	/*eslint-disable */
	if (csrf_token !== 'undefined') {
		csrfToken = csrf_token;
	}

	return csrfToken;
};
