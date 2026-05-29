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
	const isFormData = payload instanceof FormData;
	const headers = {
		'X-CSRFToken': getCookie('csrftoken'),
	};
	if (!isFormData) {
		headers['Content-Type'] = 'application/json';
	}
	const request = await fetch(fullUrl, {
		method: 'POST',
		headers,
		redirect: 'follow',
		body: isFormData ? payload : JSON.stringify(payload),
	});

	return request;
};

export const callPutApi = async ({ fullUrl, payload }) => {
	const isFormData = payload instanceof FormData;
	const headers = {
		'X-CSRFToken': getCookie('csrftoken'),
	};
	if (!isFormData) {
		headers['Content-Type'] = 'application/json';
	}
	const request = await fetch(fullUrl, {
		method: 'PUT',
		headers,
		redirect: 'follow',
		body: isFormData ? payload : JSON.stringify(payload),
	});

	return request;
};

export const callDeleteApi = async ({ fullUrl, payload }) => {
	const isFormData = payload instanceof FormData;
	const headers = {
		'X-CSRFToken': getCookie('csrftoken'),
	};
	if (!isFormData && payload) {
		headers['Content-Type'] = 'application/json';
	}
	const request = await fetch(fullUrl, {
		method: 'DELETE',
		headers,
		redirect: 'follow',
		body: isFormData ? payload : payload ? JSON.stringify(payload) : undefined,
	});

	return request;
};
