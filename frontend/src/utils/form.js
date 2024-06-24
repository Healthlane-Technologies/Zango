import forEach from 'lodash/forEach';
import isEmpty from 'lodash/isEmpty';

/**
 * Transforming formik form object data to formData
 *
 * @param {*} data - form data
 * @param {*} formData - new FormData
 * @param {*} parentKey
 * @returns modified formdata
 */
export function transformToFormData(
	data,
	formData = new FormData(),
	parentKey = null
) {
	forEach(data, (value, key) => {
		if (value === null) return;

		let formattedKey = isEmpty(parentKey) ? key : `${parentKey}[${key}]`;

		if (value instanceof File) {
			formData.set(formattedKey, value);
		} else if (value instanceof Array) {
			forEach(value, (ele) => {
				if (ele instanceof Object) {
					formData.append(`${formattedKey}`, JSON.stringify(ele));
				} else {
					formData.append(`${formattedKey}`, ele);
				}
			});
		} else if (value instanceof Object) {
			transformToFormData(value, formData, formattedKey);
		} else {
			formData.set(formattedKey, value);
		}
	});
	return formData;
}

/**
 * Transforming formik form object data to formData but nested array value will be stringified
 *
 * @param {*} data - form data
 * @param {*} formData - new FormData
 * @param {*} parentKey
 * @returns modified formdata
 */
export function transformToFormDataOrder(
	data,
	formData = new FormData(),
	parentKey = null
) {
	forEach(data, (value, key) => {
		if (value === null) return;

		let formattedKey = isEmpty(parentKey) ? key : `${parentKey}[${key}]`;

		if (value instanceof File) {
			formData.set(formattedKey, value);
		} else if (value instanceof Array) {
			formData.set(formattedKey, JSON.stringify(value));
		} else if (value instanceof Object) {
			transformToFormData(value, formData, formattedKey);
		} else {
			formData.set(formattedKey, value);
		}
	});
	return formData;
}

/**
 * Transforming formik form object data to formData, all nested array and object value will be stringified
 *
 * @param {*} data - form data
 * @param {*} formData - new FormData
 * @param {*} parentKey
 * @returns modified formdata
 */
export function transformToFormDataStringify(
	data,
	formData = new FormData(),
	parentKey = null
) {
	forEach(data, (value, key) => {
		if (value === null) return;

		let formattedKey = isEmpty(parentKey) ? key : `${parentKey}[${key}]`;

		if (value instanceof File) {
			formData.set(formattedKey, value);
		} else if (value instanceof Array) {
			formData.set(formattedKey, JSON.stringify(value));
		} else if (value instanceof Object) {
			formData.set(formattedKey, JSON.stringify(JSON.stringify(value)));
		} else {
			formData.set(formattedKey, value);
		}
	});
	return formData;
}
