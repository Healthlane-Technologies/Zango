import { useCallback } from 'react';

function AppLinkButton({ domain_url }) {
	const getDataUrl = useCallback(
		(domain_url) => {
			let port = document.location.port;
			let protocol = document.location.protocol;

			return protocol + '//' + domain_url + (port ? `:${port}` : '');
		},
		[domain_url]
	);

	const handleUrlButtonClick = (event, url) => {
		event.preventDefault();
		window.open(url, '_blank');
	};

	return (
		<button
			type="button"
			onClick={(event) => handleUrlButtonClick(event, getDataUrl(domain_url))}
			data-url={getDataUrl(domain_url)}
			className="w-fit"
		>
			<span className="font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-primary">
				{getDataUrl(domain_url)}
			</span>
		</button>
	);
}

export default AppLinkButton;
