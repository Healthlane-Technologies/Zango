"use strict";

// Class definition
var KTModalCreateProjectTeam = function () {
	// Variables
	var nextButton;
	var previousButton;
	var form;
	var stepper;

	// Private functions
	var handleForm = function() {
		nextButton.addEventListener('click', function (e) {
			// Prevent default button action
			e.preventDefault();

			// Disable button to avoid multiple click 
			nextButton.disabled = true;

			// Show loading indication
			nextButton.setAttribute('data-kt-indicator', 'on');

			// Simulate form submission
			setTimeout(function() {
				// Enable button
				nextButton.disabled = false;
				
				// Simulate form submission
				nextButton.removeAttribute('data-kt-indicator');
				
				// Go to next step
				stepper.goNext();
			}, 1500); 		
		});

		previousButton.addEventListener('click', function () {
			stepper.goPrevious();
		});
	}

	return {
		// Public functions
		init: function () {
			form = KTModalCreateProject.getForm();
			stepper = KTModalCreateProject.getStepperObj();
			nextButton = KTModalCreateProject.getStepper().querySelector('[data-kt-element="team-next"]');
			previousButton = KTModalCreateProject.getStepper().querySelector('[data-kt-element="team-previous"]');

			handleForm();
		}
	};
}();

// Webpack support
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
	window.KTModalCreateProjectTeam = module.exports = KTModalCreateProjectTeam;
}