"use strict";

// Class definition
var KTModalTwoFactorAuthentication = function () {
    // Private variables
    var modal;
    var modalObject;

    var optionsWrapper;
    var optionsSelectButton;

    var smsWrapper;
    var smsForm;
    var smsSubmitButton;
    var smsCancelButton;
    var smsValidator;

    var appsWrapper;
    var appsForm;
    var appsSubmitButton;
    var appsCancelButton;
    var appsValidator;

    // Private functions
    var handleOptionsForm = function() {
        // Handle options selection
        optionsSelectButton.addEventListener('click', function (e) {
            e.preventDefault();
            var option = optionsWrapper.querySelector('[name="auth_option"]:checked');

            optionsWrapper.classList.add('d-none');

            if (option.value == 'sms') {
                smsWrapper.classList.remove('d-none');
            } else {
                appsWrapper.classList.remove('d-none');
            }
        });
    }

	var showOptionsForm = function() {
		optionsWrapper.classList.remove('d-none');
		smsWrapper.classList.add('d-none');
		appsWrapper.classList.add('d-none');
    }

    var handleSMSForm = function() {
        // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		smsValidator = FormValidation.formValidation(
			smsForm,
			{
				fields: {
					'mobile': {
						validators: {
							notEmpty: {
								message: 'Mobile no is required'
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

        // Handle apps submition
        smsSubmitButton.addEventListener('click', function (e) {
            e.preventDefault();

			// Validate form before submit
			if (smsValidator) {
				smsValidator.validate().then(function (status) {
					console.log('validated!');

					if (status == 'Valid') {
						// Show loading indication
						smsSubmitButton.setAttribute('data-kt-indicator', 'on');

						// Disable button to avoid multiple click 
						smsSubmitButton.disabled = true;						

						// Simulate ajax process
						setTimeout(function() {
							// Remove loading indication
							smsSubmitButton.removeAttribute('data-kt-indicator');

							// Enable button
							smsSubmitButton.disabled = false;
							
							// Show success message. For more info check the plugin's official documentation: https://sweetalert2.github.io/
							Swal.fire({
								text: "Mobile number has been successfully submitted!",
								icon: "success",
								buttonsStyling: false,
								confirmButtonText: "Ok, got it!",
								customClass: {
									confirmButton: "btn btn-primary"
								}
							}).then(function (result) {
								if (result.isConfirmed) {
									modalObject.hide();
									showOptionsForm();
								}
							});

							//smsForm.submit(); // Submit form
						}, 2000);   						
					} else {
						// Show error message.
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

        // Handle sms cancelation
        smsCancelButton.addEventListener('click', function (e) {
            e.preventDefault();
            var option = optionsWrapper.querySelector('[name="auth_option"]:checked');

            optionsWrapper.classList.remove('d-none');
            smsWrapper.classList.add('d-none');
        });
    }

    var handleAppsForm = function() {
		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		appsValidator = FormValidation.formValidation(
			appsForm,
			{
				fields: {
					'code': {
						validators: {
							notEmpty: {
								message: 'Code is required'
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

        // Handle apps submition
        appsSubmitButton.addEventListener('click', function (e) {
            e.preventDefault();

			// Validate form before submit
			if (appsValidator) {
				appsValidator.validate().then(function (status) {
					console.log('validated!');

					if (status == 'Valid') {
						appsSubmitButton.setAttribute('data-kt-indicator', 'on');

						// Disable button to avoid multiple click 
						appsSubmitButton.disabled = true;

						setTimeout(function() {
							appsSubmitButton.removeAttribute('data-kt-indicator');

							// Enable button
							appsSubmitButton.disabled = false;
							
							// Show success message.
							Swal.fire({
								text: "Code has been successfully submitted!",
								icon: "success",
								buttonsStyling: false,
								confirmButtonText: "Ok, got it!",
								customClass: {
									confirmButton: "btn btn-primary"
								}
							}).then(function (result) {
								if (result.isConfirmed) {
									modalObject.hide();
									showOptionsForm();
								}
							});

							//appsForm.submit(); // Submit form
						}, 2000);   						
					} else {
						// Show error message.
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

        // Handle apps cancelation
        appsCancelButton.addEventListener('click', function (e) {
            e.preventDefault();
            var option = optionsWrapper.querySelector('[name="auth_option"]:checked');

            optionsWrapper.classList.remove('d-none');
            appsWrapper.classList.add('d-none');
        });
    }

    // Public methods
    return {
        init: function () {
            // Elements
            modal = document.querySelector('#kt_modal_two_factor_authentication');

			if (!modal) {
				return;
			}

            modalObject = new bootstrap.Modal(modal);

            optionsWrapper = modal.querySelector('[data-kt-element="options"]');
            optionsSelectButton = modal.querySelector('[data-kt-element="options-select"]');

            smsWrapper = modal.querySelector('[data-kt-element="sms"]');
            smsForm = modal.querySelector('[data-kt-element="sms-form"]');
            smsSubmitButton = modal.querySelector('[data-kt-element="sms-submit"]');
            smsCancelButton = modal.querySelector('[data-kt-element="sms-cancel"]');

            appsWrapper = modal.querySelector('[data-kt-element="apps"]');
            appsForm = modal.querySelector('[data-kt-element="apps-form"]');
            appsSubmitButton = modal.querySelector('[data-kt-element="apps-submit"]');
            appsCancelButton = modal.querySelector('[data-kt-element="apps-cancel"]');

            // Handle forms
            handleOptionsForm();
            handleSMSForm();
            handleAppsForm();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTModalTwoFactorAuthentication.init();
});
