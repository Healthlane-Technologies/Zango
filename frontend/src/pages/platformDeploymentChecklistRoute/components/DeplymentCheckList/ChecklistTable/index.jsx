import RenderValue from './RenderValue';
import EachDescriptionRow from './EachDescriptionRow';
import useApi from '../../../../../hooks/useApi';
import { useEffect, useState } from 'react';

const mapApiDataToChecklist = (apiData) => {
	return [
		{
			label: 'Debug Mode',
			description: 'Verify if Debug = False.',
			value: apiData?.DEBUG ?? false,
		},
		{
			label: 'IP Restriction',
			description:
				'Ensure App Panel access is IP-restricted. Show the allowed IPs.',
			value: apiData?.IP_RESTRICTED ?? false,
		},
		{
			label: 'Account Lockout Time',
			description:
				'Display the duration of account lockouts after failed attempts.',
			value: apiData?.ACCOUNT_LOCKOUT_TIME ?? '15 minutes',
		},
		{
			label: 'Allowed Password Attempts',
			description: 'Show the configured limit for failed login attempts.',
			value: apiData?.ALLOWED_PASSWORD_ATTEMPTS ?? 5,
		},
		{
			label: 'Password Age',
			description: 'Display the maximum age for passwords before expiration.',
			value: `${apiData?.PASSWORD_RESET_DAYS ?? 90} days`,
		},
		{
			label: 'Password Age Policies',
			description: 'Check if password age policies are in place for all users.',
			value: `Must be changed every ${apiData?.PASSWORD_RESET_DAYS ?? 90} days`,
		},
		{
			label: 'Password Strength Policies',
			description:
				'Confirm if password strength requirements (e.g., complexity, length) are enforced for all users.',
			value: `Minimum ${apiData?.PASSWORD_MIN_LENGTH ?? 12} characters`,
		},
		{
			label: 'Secure Cookies',
			description: 'Verify that cookies have secure and HttpOnly flags set.',
			value: {
				secure: apiData?.SESSION_COOKIE_SECURE ?? false,
				httpOnly: apiData?.CSRF_COOKIE_SECURE ?? false,
				sameSite: 'Strict',
			},
		},
		{
			label: 'Session Management',
			description: 'Session security configuration.',
			value: {
				expireOnBrowserClose: apiData?.SESSION_EXPIRE_AT_BROWSER_CLOSE ?? false,
				warnAfter: `${apiData?.SESSION_SECURITY_WARN_AFTER ?? 1700} seconds`,
				expireAfter: `${
					apiData?.SESSION_SECURITY_EXPIRE_AFTER ?? 1800
				} seconds`,
			},
		},
	];
};

function CheckListTable() {
	const [checklistItems, setchecklistItems] = useState([]);
	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				setchecklistItems(mapApiDataToChecklist(response.settings));
			}
		};
		makeApiCall();
	}, []);

	return (
		<table data-cy="app_details" className="w-fit border-spacing-x-4">
			<tbody>
				{checklistItems.map((item, index) => (
					<EachDescriptionRow
						key={index}
						label={item.label}
						content={<RenderValue value={item.value} />}
					/>
				))}
			</tbody>
		</table>
	);
}

export default CheckListTable;
