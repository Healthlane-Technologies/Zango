import imageCompression from 'browser-image-compression';
import forEach from 'lodash/forEach';
import isEmpty from 'lodash/isEmpty';
import { useLayoutEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';

export function isDev() {
	if (!process.env.NODE_ENV || process.env.NODE_ENV === 'development') {
		return true;
	} else {
		return false;
	}
}

export function classNames(...classes) {
	return classes.filter(Boolean).join(' ');
}

export const isHcpDashboard = window.location.pathname.includes(
	'/app/hcp/dashboard/'
);

export const HCP_MENU_ITEMS = [
	{ label: 'Profile', link: '/msdodtrack038/profile' },
];

export const STOCKIST_MENU_ITEMS = [
	{ label: 'Profile', link: '/msdodtrack038/profile' },
];

export const INITIATE_EYC_MENU_ITEMS = [];

export const SHOW_PROFILE_MENU_ITEMS = [];

export function transformToFormData(
	data,
	formData = new FormData(),
	parentKey = null
) {
	// console.log(data);
	forEach(data, (value, key) => {
		if (value === null) return; // else "null" will be added

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
	// console.log(data);
	forEach(data, (value, key) => {
		if (value === null) return; // else "null" will be added

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
	// console.log(data);
	forEach(data, (value, key) => {
		if (value === null) return; // else "null" will be added

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

export function transformToDynamicFormData(
	data,
	formData = new FormData(),
	parentKey = null
) {
	let tempData = data;
	forEach(tempData, (value, key) => {
		if (value === null) return; // else "null" will be added

		if (value instanceof File) {
			formData.set(key, value);
			if (key) {
				delete tempData[key];
			}
		}
	});

	formData.set('data', JSON.stringify(tempData));
	return formData;
}

export function cardinalToOrdinal(number) {
	let modOf10 = number % 10,
		modOf100 = number % 100;
	if (modOf10 == 1 && modOf100 != 11) {
		return number + 'st';
	}
	if (modOf10 == 2 && modOf100 != 12) {
		return number + 'nd';
	}
	if (modOf10 == 3 && modOf100 != 13) {
		return number + 'rd';
	}
	return number + 'th';
}

export const handleFileUpload = async (event, formik, formik_field) => {
	const imageFile = event.target.files[0];

	const options = {
		maxSizeMB: 1,
		maxWidthOrHeight: 1920,
		useWebWorker: true,
	};
	try {
		const compressedFile = await imageCompression(imageFile, options);
		formik.setFieldValue(formik_field, compressedFile);
	} catch (error) {
		console.log(error);
	}
};

function debounce(func, timeout = 0) {
	let timer;
	return (...args) => {
		clearTimeout(timer);
		timer = setTimeout(() => {
			func.apply(this, args);
		}, timeout);
	};
}

function updateSize() {
	let vh = window.innerHeight * 0.01;
	document.documentElement.style.setProperty('--vh', `${vh}px`);
	document.documentElement.style.setProperty(
		'--app-height',
		`${window.innerHeight}px`
	);
}

const heightChange = debounce(() => updateSize());

export function useWindowSizeHeight() {
	useLayoutEffect(() => {
		window.addEventListener('resize', heightChange);
		heightChange();
		return () => window.removeEventListener('resize', heightChange);
	}, []);
}

export function useQuery() {
	const { search } = useLocation();

	return useMemo(() => new URLSearchParams(search), [search]);
}

export const currencyFormatter = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'INR',
});

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

export const getPlatformVersion = () => {
	let platformVersion = '';

	/*eslint-disable */
	if (platform_version !== 'undefined') {
		platformVersion = platform_version;
	}

	return platformVersion;
};
