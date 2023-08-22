"use strict";

// Class definition
var KTAccountSettingsDeactivateAccount = function () {
    // Private variables
    var form;
    var validation;
    var submitButton;

    // Private functions
    var initValidation = function () {
        // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
        validation = FormValidation.formValidation(
            form,
            {
                fields: {
                    deactivate: {
                        validators: {
                            notEmpty: {
                                message: 'Please check the box to deactivate your account'
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    submitButton: new FormValidation.plugins.SubmitButton(),
                    //defaultSubmit: new FormValidation.plugins.DefaultSubmit(), // Uncomment this line to enable normal button submit after form validation
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }
        );
    }

    var handleForm = function () {
        submitButton.addEventListener('click', function (e) {
            e.preventDefault();

            validation.validate().then(function (status) {
                if (status == 'Valid') {

                    swal.fire({
                        text: "Are you sure you would like to deactivate your account?",
                        icon: "warning",
                        buttonsStyling: false,
                        showDenyButton: true,
                        confirmButtonText: "Yes",
                        denyButtonText: 'No',
                        customClass: {
                            confirmButton: "btn btn-light-primary",
                            denyButton: "btn btn-danger"
                        }
                    }).then((result) => {
                        if (result.isConfirmed) {
                            Swal.fire({
                                text: 'Your account has been deactivated.', 
                                icon: 'success',
                                confirmButtonText: "Ok",
                                buttonsStyling: false,
                                customClass: {
                                    confirmButton: "btn btn-light-primary"
                                }
                            })
                        } else if (result.isDenied) {
                            Swal.fire({
                                text: 'Account not deactivated.', 
                                icon: 'info',
                                confirmButtonText: "Ok",
                                buttonsStyling: false,
                                customClass: {
                                    confirmButton: "btn btn-light-primary"
                                }
                            })
                        }
                    });

                } else {
                    swal.fire({
                        text: "Sorry, looks like there are some errors detected, please try again.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-light-primary"
                        }
                    });
                }
            });
        });
    }

    // Public methods
    return {
        init: function () {
            form = document.querySelector('#kt_account_deactivate_form');

            if (!form) {
                return;
            }
            
            submitButton = document.querySelector('#kt_account_deactivate_account_submit');

            initValidation();
            handleForm();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTAccountSettingsDeactivateAccount.init();
});
