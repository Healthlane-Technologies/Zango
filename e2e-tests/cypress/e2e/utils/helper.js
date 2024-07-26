import appPanelPageObjects from '../../support/pageObjectModel/appPanelPageObjects';

export function error_message() {
	//expect($error).to.be.visible;
	appPanelPageObjects.getErrorMessage().should('contain', 'Required');
}
