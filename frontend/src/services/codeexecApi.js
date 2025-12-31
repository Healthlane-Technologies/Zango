import { callGetApi, callPostApi, callPutApi, callDeleteApi } from './api';

const BASE_URL = '/api/v1/apps';

/**
 * Get all code executions with optional search and pagination
 */
export const getCodeExecutions = async (appId, { page = 1, pageSize = 20, search = '' } = {}) => {
	const queryParams = new URLSearchParams({
		page: page.toString(),
		page_size: pageSize.toString(),
		search: search,
	});

	const response = await callGetApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/?${queryParams.toString()}`,
	});

	return response;
};

/**
 * Get code execution details by ID
 */
export const getCodeExecutionDetail = async (appId, codeexecId) => {
	const response = await callGetApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/?codeexec_id=${codeexecId}`,
	});

	return response;
};

/**
 * Get execution history for a code execution
 */
export const getExecutionHistory = async (appId, codeexecId) => {
	const response = await callGetApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/?action=get_execution_history&codeexec_id=${codeexecId}`,
	});

	return response;
};

/**
 * Create new code execution
 */
export const createCodeExecution = async (appId, payload) => {
	const response = await callPostApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/`,
		payload: payload,
	});

	return response;
};

/**
 * Update existing code execution
 */
export const updateCodeExecution = async (appId, codeexecId, payload) => {
	const response = await callPutApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/?codeexec_id=${codeexecId}`,
		payload: payload,
	});

	return response;
};

/**
 * Delete code execution
 */
export const deleteCodeExecution = async (appId, codeexecId) => {
	const response = await callDeleteApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/?codeexec_id=${codeexecId}`,
		payload: {},
	});

	return response;
};

/**
 * Execute code asynchronously
 */
export const executeCode = async (appId, codeexecId) => {
	const response = await callPostApi({
		fullUrl: `${BASE_URL}/${appId}/codeexec/execute/?codeexec_id=${codeexecId}`,
		payload: {},
	});

	return response;
};
