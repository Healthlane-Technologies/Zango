// import { decamelizeKeys } from 'humps';
import { getCookie, isHcpDashboard } from '../utils/helper';
let authToken =
	'5kO5NUSSG6SFZctca1dVJwMMbK14vfS0ECed9xlGcwNP1jeeYfN6k3l4uqe7sF7C';

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

// export const initializeDashboard = {
// 	url: isHcpDashboard
// 		? '/hcp/initialize-dashboard/'
// 		: '/patient/initialize-dashboard/',
// 	type: 'GET',
// };

// export const getProgramDetails = (tenantCode) => ({
// 	url: isHcpDashboard
// 		? `/hcp/get-programs/${tenantCode}/`
// 		: `/patient/get-programs/${tenantCode}/`,
// 	type: 'GET',
// });

// export const workflow = (payload) => ({
// 	url: isHcpDashboard ? `/hcp/workflow/` : '/patient/workflow/',
// 	type: 'POST',
// 	payload,
// });

// export const patientTable = (tenantCode, searchValue, pageNumber) => ({
// 	url: `/hcp/patient-table/${tenantCode}/?page=${pageNumber}&search_value=${searchValue}`,
// 	type: 'GET',
// });

// export const getPatientDetails = (tenantCode, patientId) => ({
// 	url: `/hcp/patient-programs/${tenantCode}/${patientId}`,
// 	type: 'GET',
// });

// export const patientSearch = (payload) => ({
// 	url: '/hcp/patient-search/',
// 	type: 'POST',
// 	payload,
// 	loader: false,
// });
