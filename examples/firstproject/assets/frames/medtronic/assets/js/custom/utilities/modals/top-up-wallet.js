"use strict";

// Class definition
var KTModalTopUpWallet = function () {
	// Elements
	var modal;
	var modalEl;

	var stepper;
	var form;
	var formSubmitButton;
	var formContinueButton;

	// Variables
	var stepperObj;
	var validations = [];

	// Private Functions
	var initStepper = function () {
		// Initialize Stepper
		stepperObj = new KTStepper(stepper);

		// Stepper change event(handle hiding submit button for the last step)
		stepperObj.on('kt.stepper.changed', function (stepper) {
			if (stepperObj.getCurrentStepIndex() === 4) {
				formSubmitButton.classList.remove('d-none');
				formSubmitButton.classList.add('d-inline-block');
				formContinueButton.classList.add('d-none');
			} else if (stepperObj.getCurrentStepIndex() === 5) {
				formSubmitButton.classList.add('d-none');
				formContinueButton.classList.add('d-none');
			} else {
				formSubmitButton.classList.remove('d-inline-block');
				formSubmitButton.classList.remove('d-none');
				formContinueButton.classList.remove('d-none');
			}
		});

		// Validation before going to next page
		stepperObj.on('kt.stepper.next', function (stepper) {
			console.log('stepper.next');

			// Validate form before change stepper step
			var validator = validations[stepper.getCurrentStepIndex() - 1]; // get validator for currnt step

			if (validator) {
				validator.validate().then(function (status) {
					console.log('validated!');

					if (status == 'Valid') {
						stepper.goNext();

						//KTUtil.scrollTop();
					} else {
						// Show error message popup. For more info check the plugin's official documentation: https://sweetalert2.github.io/
						Swal.fire({
							text: "Sorry, looks like there are some errors detected, please try again.",
							icon: "error",
							buttonsStyling: false,
							confirmButtonText: "Ok, got it!",
							customClass: {
								confirmButton: "btn btn-light"
							}
						}).then(function () {
							//KTUtil.scrollTop();
						});
					}
				});
			} else {
				stepper.goNext();

				KTUtil.scrollTop();
			}
		});

		// Prev event
		stepperObj.on('kt.stepper.previous', function (stepper) {
			console.log('stepper.previous');

			stepper.goPrevious();
			KTUtil.scrollTop();
		});

		formSubmitButton.addEventListener('click', function (e) {
			// Prevent default button action
			e.preventDefault();

			// Disable button to avoid multiple click 
			formSubmitButton.disabled = true;

			// Show loading indication
			formSubmitButton.setAttribute('data-kt-indicator', 'on');

			// Simulate form submission
			setTimeout(function () {
				// Hide loading indication
				formSubmitButton.removeAttribute('data-kt-indicator');

				// Enable button
				formSubmitButton.disabled = false;

				stepperObj.goNext();
				//KTUtil.scrollTop();
			}, 2000);
		});
	}

	// Init form inputs
	var initForm = function () {	
        // Handle currency swap logic
        const currencyTypes = form.querySelectorAll('[name="currency_type"]');
        const targets = form.querySelectorAll('[data-kt-modal-top-up-wallet-option]');
        let value = "dollar";
        currencyTypes.forEach(currency => {
            currency.addEventListener('change', e => {
                value = e.target.value;

                targets.forEach(target => {
                    target.classList.add('d-none');

                    if(target.getAttribute('data-kt-modal-top-up-wallet-option') === value){
                        target.classList.remove('d-none');
                    }
                });
            });
        });

		// Handle top up wallet button
		const restartButton = document.querySelector('#kt_modal_top_up_wallet_create_new');
		restartButton.addEventListener('click', function () {
			form.reset();
			stepperObj.goTo(1);
		});
	}

	// Init validation
	var initValidation = function () {
		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		// Step 1
		validations.push(FormValidation.formValidation(
			form,
			{
				fields: {
					top_up_amount: {
						validators: {
							notEmpty: {
								message: 'Top up amount is required'
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
		));

        // Step 2
		validations.push(FormValidation.formValidation(
			form,
			{
				fields: {
					payment_methods: {
						validators: {
							notEmpty: {
								message: 'Payment method is required'
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
		));

        // Step 3
		validations.push(FormValidation.formValidation(
			form,
			{
				fields: {
					top_up_password: {
						validators: {
							notEmpty: {
								message: 'Password is required'
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
		));
	}

	// Handle cancel modal
    const handleCancelAction = () => {
        const closeButton = modalEl.querySelector('[data-kt-modal-action-type="close"]');
        closeButton.addEventListener('click', e => {
            cancelAction(e);
        });

        const cancelAction = (e) => {
            e.preventDefault();

            Swal.fire({
                text: "Are you sure you would like to cancel?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "Yes, cancel it!",
                cancelButtonText: "No, return",
                customClass: {
                    confirmButton: "btn btn-primary",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    form.reset(); // Reset form	
                    modal.hide(); // Hide modal				
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "Your form has not been cancelled!.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary",
                        }
                    });
                }
            });
        }
    }

	return {
		// Public Functions
		init: function () {
			// Elements
			modalEl = document.querySelector('#kt_modal_top_up_wallet');

			if (!modalEl) {
				return;
			}

			modal = new bootstrap.Modal(modalEl);

			stepper = document.querySelector('#kt_modal_top_up_wallet_stepper');
			form = document.querySelector('#kt_modal_top_up_wallet_stepper_form');
			formSubmitButton = stepper.querySelector('[data-kt-stepper-action="submit"]');
			formContinueButton = stepper.querySelector('[data-kt-stepper-action="next"]');

			initStepper();
			initForm();
			initValidation();
			handleCancelAction();
		}
	};
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
	KTModalTopUpWallet.init();
});
