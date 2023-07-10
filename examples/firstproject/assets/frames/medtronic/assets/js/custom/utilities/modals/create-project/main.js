"use strict";

// Class definition
var KTModalCreateProject = function () {
	// Private variables
	var stepper;
	var stepperObj;
	var form;	

	// Private functions
	var initStepper = function () {
		// Initialize Stepper
		stepperObj = new KTStepper(stepper);
	}

	return {
		// Public functions
		init: function () {
			stepper = document.querySelector('#kt_modal_create_project_stepper');
			form = document.querySelector('#kt_modal_create_project_form');

			initStepper();
		},

		getStepperObj: function () {
			return stepperObj;
		},

		getStepper: function () {
			return stepper;
		},
		
		getForm: function () {
			return form;
		}
	};
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
	if (!document.querySelector('#kt_modal_create_project')) {
		return;
	}

	KTModalCreateProject.init();
	KTModalCreateProjectType.init();
	KTModalCreateProjectBudget.init();
	KTModalCreateProjectSettings.init();
	KTModalCreateProjectTeam.init();
	KTModalCreateProjectTargets.init();
	KTModalCreateProjectFiles.init();
	KTModalCreateProjectComplete.init();
});

// Webpack support
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
	window.KTModalCreateProject = module.exports = KTModalCreateProject;
}
