"use strict";

// Class definition
var KTModalCreateProjectBudget = function () {
	// Variables
	var nextButton;
	var previousButton;
	var validator;
	var form;
	var stepper;

	// Private functions
	var initValidation = function() {
		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		validator = FormValidation.formValidation(
			form,
			{
				fields: {
					'budget_setup': {
						validators: {
							notEmpty: {
								message: 'Budget amount is required'
							},
							callback: {
								message: 'The budget amount must be greater than $100',
								callback: function(input) {
									var currency = input.value;
									currency = currency.replace(/[$,]+/g,"");

									if (parseFloat(currency) < 100) {
										return false;
									}
								}
							}
						}
					},
					'budget_usage': {
						validators: {
							notEmpty: {
								message: 'Budget usage type is required'
							}
						}
					},
					'budget_allow': {
						validators: {
							notEmpty: {
								message: 'Allowing budget is required'
							}
						}
					}
				},
				
				plugins: {
					trigger: new FormValidation.plugins.Trigger(),
					bootstrap: new FormValidation.plugins.Bootstrap5({
						rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
					})
				}
			}
		);

		// Revalidate on change
		KTDialer.getInstance(form.querySelector('#kt_modal_create_project_budget_setup')).on('kt.dialer.changed', function() {
			// Revalidate the field when an option is chosen
            validator.revalidateField('budget_setup');
		});
	}

	var handleForm = function() {
		nextButton.addEventListener('click', function (e) {
			// Prevent default button action
			e.preventDefault();

			// Disable button to avoid multiple click 
			nextButton.disabled = true;

			// Validate form before submit
			if (validator) {
				validator.validate().then(function (status) {
					console.log('validated!');

					if (status == 'Valid') {
						// Show loading indication
						nextButton.setAttribute('data-kt-indicator', 'on');

						// Simulate form submission
						setTimeout(function() {
							// Simulate form submission
							nextButton.removeAttribute('data-kt-indicator');

							// Enable button
							nextButton.disabled = false;
							
							// Go to next step
							stepper.goNext();
						}, 1500);   						
					} else {
						// Enable button
						nextButton.disabled = false;

						// Show popup warning. For more info check the plugin's official documentation: https://sweetalert2.github.io/
						Swal.fire({
							text: "Sorry, looks like there are some errors detected, please try again.",
							icon: "error",
							buttonsStyling: false,
							confirmButtonText: "Ok, got it!",
							customClass: {
								confirmButton: "btn btn-primary"
							}
						});
					}
				});
			}			
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
			nextButton = KTModalCreateProject.getStepper().querySelector('[data-kt-element="budget-next"]');
			previousButton = KTModalCreateProject.getStepper().querySelector('[data-kt-element="budget-previous"]');

			initValidation();
			handleForm();
		}
	};
}();

// Webpack support
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
	window.KTModalCreateProjectBudget = module.exports = KTModalCreateProjectBudget;
}
