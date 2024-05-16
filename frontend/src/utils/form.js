import forEach from 'lodash/forEach';
import isEmpty from 'lodash/isEmpty';

// TODO: Add function comments
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
