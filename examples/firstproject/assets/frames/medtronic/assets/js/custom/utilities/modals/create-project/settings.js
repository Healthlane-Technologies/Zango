"use strict";

// Class definition
var KTModalCreateProjectSettings = function () {
	// Variables
	var nextButton;
	var previousButton;
	var validator;
	var form;
	var stepper;

	// Private functions
	var initForm = function() {
		// Project logo
		// For more info about Dropzone plugin visit:  https://www.dropzonejs.com/#usage
		var myDropzone = new Dropzone("#kt_modal_create_project_settings_logo", { 
			url: "https://keenthemes.com/scripts/void.php", // Set the url for your upload script location
            paramName: "file", // The name that will be used to transfer the file
            maxFiles: 10,
            maxFilesize: 10, // MB
            addRemoveLinks: true,
            accept: function(file, done) {
                if (file.name == "justinbieber.jpg") {
                    done("Naha, you don't.");
                } else {
                    done();
                }
            }
		});  

		// Due date. For more info, please visit the official plugin site: https://flatpickr.js.org/
		var releaseDate = $(form.querySelector('[name="settings_release_date"]'));
		releaseDate.flatpickr({
			enableTime: true,
			dateFormat: "d, M Y, H:i",
		});

		// Expiry year. For more info, plase visit the official plugin site: https://select2.org/
        $(form.querySelector('[name="settings_customer"]')).on('change', function() {
            // Revalidate the field when an option is chosen
            validator.revalidateField('settings_customer');
        });
	}

	var initValidation = function() {
		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		validator = FormValidation.formValidation(
			form,
			{
				fields: {
					'settings_name': {
						validators: {
							notEmpty: {
								message: 'Project name is required'
							}
						}
					},
					'settings_customer': {
						validators: {
							notEmpty: {
								message: 'Customer is required'
							}
						}
					},
					'settings_description': {
						validators: {
							notEmpty: {
								message: 'Description is required'
							}
						}
					},
					'settings_release_date': {
						validators: {
							notEmpty: {
								message: 'Release date is required'
							}
						}
					},
					'settings_notifications[]': {
						validators: {
							notEmpty: {
								message: 'Notifications are required'
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
			// Go to previous step
			stepper.goPrevious();
		});
	}

	return {
		// Public functions
		init: function () {
			form = KTModalCreateProject.getForm();
			stepper = KTModalCreateProject.getStepperObj();
			nextButton = KTModalCreateProject.getStepper().querySelector('[data-kt-element="settings-next"]');
			previousButton = KTModalCreateProject.getStepper().querySelector('[data-kt-element="settings-previous"]');

			initForm();
			initValidation();
			handleForm();
		}
	};
}();

// Webpack support
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
	window.KTModalCreateProjectSettings = module.exports = KTModalCreateProjectSettings;
}
