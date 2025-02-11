import RenderValue from './RenderValue';
import EachDescriptionRow from './EachDescriptionRow';

const DEPLOYMENT_CHECKLIST = [
	{
		label: 'Debug Mode',
		description: 'Verify if Debug = False.',
		value: false,
	},
	{
		label: 'IP Restriction',
		description:
			'Ensure App Panel access is IP-restricted. Show the allowed IPs.',
		value: ['192.168.1.1', '10.0.0.2'],
	},
	{
		label: 'Account Lockout Time',
		description:
			'Display the duration of account lockouts after failed attempts.',
		value: '15 minutes',
	},
	{
		label: 'Allowed Password Attempts',
		description: 'Show the configured limit for failed login attempts.',
		value: 5,
	},
	{
		label: 'Password Age',
		description: 'Display the maximum age for passwords before expiration.',
		value: '90 days',
	},
	{
		label: 'HTTPS Only',
		description: 'Verify if HTTPS-only is enforced.',
		value: true,
	},
	{
		label: 'Password Age Policies',
		description: 'Check if password age policies are in place for all users.',
		value: 'Must be changed every 90 days',
	},
	{
		label: 'Password Strength Policies',
		description:
			'Confirm if password strength requirements (e.g., complexity, length) are enforced for all users.',
		value:
			'Minimum 12 characters, includes uppercase, lowercase, number, special character',
	},
	{
		label: 'Default IDs or Passwords',
		description: 'Ensure no default IDs or passwords are active in production.',
		value: 'None',
	},
	{
		label: 'Concurrent Sessions Disabled',
		description:
			'Verify if concurrent sessions are disallowed to prevent session hijacking.',
		value: true,
	},
	{
		label: 'Server Time Synchronization',
		description: 'Confirm if the server time is synchronized with NTP.',
		value: true,
	},
	{
		label: 'Two-Factor Authentication (2FA)',
		description:
			'Check if 2FA is enforced for all user accounts in applications.',
		value: true,
	},
	{
		label: 'SSO/OIDC',
		description:
			'Verify if users SSO/OIDC is enforced for all application users.',
		value: true,
	},
	{
		label: 'Cross-Site Scripting (XSS) Protection',
		description:
			'Verify if XSS protection headers are enabled in the HTTP response (e.g., X-XSS-Protection).',
		value: true,
	},
	{
		label: 'Content Security Policy (CSP)',
		description:
			'Ensure a Content Security Policy is set to help prevent data injection attacks like XSS.',
		value: "default-src 'self'; script-src 'self' 'trusted-scripts.com'",
	},
	{
		label: 'SQL Injection Protection',
		description:
			'Confirm that prepared statements or ORM protections are in place to prevent SQL injection vulnerabilities.',
		value: true,
	},
	{
		label: 'Clickjacking Protection',
		description:
			'Check for X-Frame-Options headers to prevent clickjacking attacks.',
		value: 'DENY',
	},
	{
		label: 'Secure Cookies',
		description:
			'Verify that cookies have secure and HttpOnly flags set to prevent access by JavaScript and ensure they’re sent only over HTTPS.',
		value: {
			secure: true,
			httpOnly: true,
			sameSite: 'Strict',
		},
	},
	{
		label: 'API Rate Limiting',
		description:
			'Ensure API endpoints have rate-limiting mechanisms to mitigate brute-force and DoS attacks.',
		value: '100 requests per minute per IP',
	},
	{
		label: 'Audit Logging',
		description:
			'Confirm if audit logging is enabled for critical actions (e.g., login attempts, password changes, sensitive data access).',
		value: true,
	},
	{
		label: 'Data Encryption in Transit',
		description:
			'Verify that data in transit is encrypted, typically with TLS, for secure communication.',
		value: 'TLS 1.2+',
	},
	{
		label: 'Security Headers Compliance',
		description:
			'Check for other essential HTTP security headers (e.g., Strict-Transport-Security, X-Content-Type-Options, Referrer-Policy).',
		value: [
			'Strict-Transport-Security: max-age=31536000; includeSubDomains',
			'X-Content-Type-Options: nosniff',
			'Referrer-Policy: no-referrer',
		],
	},
	{
		label: 'External Resources Control',
		description:
			'Confirm that only trusted and necessary external resources (e.g., JavaScript libraries, stylesheets) are allowed.',
		value: ['trusted-cdn.com', 'secure-fonts.com'],
	},
];


function CheckListTable() {
	return (
		<table data-cy="app_details" className="w-fit border-spacing-x-4">
			<tbody>
				{DEPLOYMENT_CHECKLIST.map((item, index) => (
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
