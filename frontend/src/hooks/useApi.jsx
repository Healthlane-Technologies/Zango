import { useCallback, useContext } from 'react';
import { callGetApi, callPostApi, callPutApi } from '../services/api';
import { ErrorMessageContext } from '../context/ErrorMessageContextProvider';
import { LoaderContext } from '../context/LoaderContextProvider';
import toast from 'react-hot-toast';
import Notifications from '../components/Notifications';

const notify = (type, title, description) =>
	toast.custom(
		(t) => (
			<Notifications
				type={type}
				toastRef={t}
				title={title}
				description={description}
			/>
		),
		{
			duration: 5000,
			position: 'bottom-left',
		}
	);

/**
 * This hook automatically appends the zelthy authentication token to network requests made
 *
 * @returns {function} triggerApi which takes in
 * @param {object} apiDetails consisting of URL and request type
 */
export default function useApi() {
	const { setLoading } = useContext(LoaderContext);
	const setErrorMessage = useContext(ErrorMessageContext);

	const triggerApi = useCallback(
		async (apiDetails) => {
			let apiRequest = undefined;

			if (apiDetails.loader !== false) {
				setLoading(true);
			}

			switch (apiDetails.type) {
				case 'POST':
					apiRequest = await callPostApi({
						fullUrl: apiDetails.url,
						payload: apiDetails.payload,
					});
					break;
				case 'PUT':
					apiRequest = await callPutApi({
						fullUrl: apiDetails.url,
						payload: apiDetails.payload,
					});
					break;
				case 'GET':
					apiRequest = await callGetApi({
						fullUrl: apiDetails.url,
					});
					break;
				default:
					apiRequest = await callGetApi({
						fullUrl: apiDetails.url,
					});
			}

			if (apiDetails.loader !== false) {
				setLoading(false);
			}

			if (apiRequest.status === 200) {
				try {
					// if (apiRequest.redirected) {
					// 	if (apiRequest.url.indexOf('login') !== -1) {
					// 		window.location = apiRequest.url;
					// 	}
					// }
					const { response, success } = await apiRequest.json();

					if (!success) {
						setErrorMessage(response?.message || 'Server Error');
					} else {
						if (apiDetails?.notify) {
							notify('success', 'Success', response.message);
						}
					}

					return {
						response: response,
						success,
						responseStatus: apiRequest.status,
					};
				} catch (error) {
					setErrorMessage('Server Error');

					return {
						response: {
							message: 'Server Error',
						},
						success: false,
						responseStatus: apiRequest.status,
					};
				}
			} else if (apiRequest.status === 400) {
				try {
					const { response, success } = await apiRequest.json();

					setErrorMessage(response.message);

					return {
						response: {
							message: 'Server Error',
						},
						success: false,
						responseStatus: apiRequest.status,
					};
				} catch (error) {
					notify('error', 'Success', 'Server Error');

					return {
						response: {
							message: 'Server Error',
						},
						success: false,
						responseStatus: apiRequest.status,
					};
				}
			} else {
				setErrorMessage('Server Error');

				return {
					response: {
						message: 'Server Error',
					},
					success: false,
					responseStatus: apiRequest.status,
				};
			}
		},
		[setLoading, setErrorMessage]
	);

	return triggerApi;
}
