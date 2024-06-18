import { getCookie } from '../utils/helper';

export const callGetApi = async ({ fullUrl }) => {
	const request = await fetch(fullUrl, {
		method: 'GET',
		headers: {
			'X-CSRFToken': getCookie('csrftoken'),
		},
		redirect: 'follow',
	});
	return request;
};

export const callPostApi = async ({ fullUrl, payload }) => {
	const request = await fetch(fullUrl, {
		method: 'POST',
		headers: {
			'X-CSRFToken': getCookie('csrftoken'),
		},
		redirect: 'follow',
		body: payload instanceof FormData ? payload : JSON.stringify(payload),
	});

	return request;
};

export const callPutApi = async ({ fullUrl, payload }) => {
	const request = await fetch(fullUrl, {
		method: 'PUT',
		headers: {
			'X-CSRFToken': getCookie('csrftoken'),
		},
		redirect: 'follow',
		body: payload instanceof FormData ? payload : JSON.stringify(payload),
	});

	return request;
};

export const callDeleteApi = async ({ fullUrl, payload }) => {
	const request = await fetch(fullUrl, {
		method: 'DELETE',
		headers: {
			'X-CSRFToken': getCookie('csrftoken'),
		},
		redirect: 'follow',
		body: payload instanceof FormData ? payload : JSON.stringify(payload),
	});

	return request;
};
