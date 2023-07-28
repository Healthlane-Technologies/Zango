import moment from 'moment';

export function formatLaunchDate(date) {
	return moment(date, 'DD/MM/YYYY').format("DD MMM' YY");
}

export function getTimeFromNow(date) {
	return moment(date, 'DD/MM/YYYY').fromNow();
}
