"use strict";

// Class definition
var KTModalAdjustBalance = function () {
    var element;
    var submitButton;
    var cancelButton;
    var closeButton;
    var validator;
    var maskInput;
    var newBalance;
    var form;
    var modal;

    // Init form inputs
    var initForm = function () {
        // Init inputmask plugin --- For more info please refer to the official documentation here: https://github.com/RobinHerbots/Inputmask
        Inputmask("US$ 9,999,999.99", {
            "numericInput": true
        }).mask("#kt_modal_inputmask");
    }

    var handleBalanceCalculator = function () {
        // Select elements
        const currentBalance = element.querySelector('[kt-modal-adjust-balance="current_balance"]');
        newBalance = element.querySelector('[kt-modal-adjust-balance="new_balance"]');
        maskInput = document.getElementById('kt_modal_inputmask');

        // Get current balance value
        const isNegative = currentBalance.innerHTML.includes('-');
        let currentValue = parseFloat(currentBalance.innerHTML.replace(/[^0-9.]/g, '').replace(',', ''));
        currentValue = isNegative ? currentValue * -1 : currentValue; 

        // On change event for inputmask
        let maskValue;
        maskInput.addEventListener('focusout', function (e) {
            // Get inputmask value on change
            maskValue = parseFloat(e.target.value.replace(/[^0-9.]/g, '').replace(',', ''));

            // Set mask value as 0 when NaN detected
            if(isNaN(maskValue)){
                maskValue = 0;
            }

            // Calculate & set new balance value
            newBalance.innerHTML = 'US$ ' + (maskValue + currentValue).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
        });
    }

    // Handle form validation and submittion
    var handleForm = function () {
        // Stepper custom navigation

        // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
        validator = FormValidation.formValidation(
            form,
            {
                fields: {
                    'adjustment': {
                        validators: {
                            notEmpty: {
                                message: 'Adjustment type is required'
                            }
                        }
                    },
                    'amount': {
                        validators: {
                            notEmpty: {
                                message: 'Amount is required'
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

        // Revalidate country field. For more info, plase visit the official plugin site: https://select2.org/
        $(form.querySelector('[name="adjustment"]')).on('change', function () {
            // Revalidate the field when an option is chosen
            validator.revalidateField('adjustment');
        });

        // Action buttons
        submitButton.addEventListener('click', function (e) {
            // Prevent default button action
            e.preventDefault();

            // Validate form before submit
            if (validator) {
                validator.validate().then(function (status) {
                    console.log('validated!');

                    if (status == 'Valid') {
                        // Show loading indication
                        submitButton.setAttribute('data-kt-indicator', 'on');

                        // Disable submit button whilst loading
                        submitButton.disabled = true;

                        // Simulate form submission
                        setTimeout(function () {
                            // Simulate form submission
                            submitButton.removeAttribute('data-kt-indicator');

                            // Show popup confirmation 
                            Swal.fire({
                                text: "Form has been successfully submitted!",
                                icon: "success",
                                buttonsStyling: false,
                                confirmButtonText: "Ok, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            }).then(function (result) {
                                if (result.isConfirmed) {
                                    modal.hide();

                                    // Enable submit button after loading
                                    submitButton.disabled = false;

                                    // Reset form for demo purposes only
                                    form.reset();
                                    newBalance.innerHTML = "--";
                                }
                            });

                            //form.submit(); // Submit form
                        }, 2000);
                    } else {
                        // Show popup warning 
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

        cancelButton.addEventListener('click', function (e) {
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
        });

        closeButton.addEventListener('click', function (e) {
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
        });
    }
    
    return {
        // Public functions
        init: function () {
            // Elements
            element = document.querySelector('#kt_modal_adjust_balance');
            modal = new bootstrap.Modal(element);

            form = element.querySelector('#kt_modal_adjust_balance_form');
            submitButton = form.querySelector('#kt_modal_adjust_balance_submit');
            cancelButton = form.querySelector('#kt_modal_adjust_balance_cancel');
            closeButton = element.querySelector('#kt_modal_adjust_balance_close');

            initForm();
            handleBalanceCalculator();
            handleForm();
        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTModalAdjustBalance.init();
});