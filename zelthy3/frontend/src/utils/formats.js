import moment from 'moment';

export function formatLaunchDate(date) {
	return moment(date).format("DD MMM' YY");
}

export function formatTableDate(date) {
	return moment(date).format('DD MMM, YYYY');
}

export function getTimeFromNow(date) {
	return moment(date).fromNow();
}

export function isRecentlyLaunched(date) {
	let presentDate = moment();
	let differenceInDays = presentDate.diff(moment(date), 'days');
	if (differenceInDays <= 7) {
		return true;
	} else {
		return false;
	}
}
