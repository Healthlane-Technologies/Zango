"use strict";

// Class definition
var KTUsersViewMain = function () {

    // Init login session button
    var initLoginSession = () => {
        const button = document.getElementById('kt_modal_sign_out_sesions');

        button.addEventListener('click', e => {
            e.preventDefault();

            Swal.fire({
                text: "Are you sure you would like sign out all sessions?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "Yes, sign out!",
                cancelButtonText: "No, return",
                customClass: {
                    confirmButton: "btn btn-primary",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    Swal.fire({
                        text: "You have signed out all sessions!.",
                        icon: "success",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary",
                        }
                    });
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "Your sessions are still preserved!.",
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


    // Init sign out single user
    var initSignOutUser = () => {
        const signOutButtons = document.querySelectorAll('[data-kt-users-sign-out="single_user"]');

        signOutButtons.forEach(button => {
            button.addEventListener('click', e => {
                e.preventDefault();

                const deviceName = button.closest('tr').querySelectorAll('td')[1].innerText;

                Swal.fire({
                    text: "Are you sure you would like sign out " + deviceName + "?",
                    icon: "warning",
                    showCancelButton: true,
                    buttonsStyling: false,
                    confirmButtonText: "Yes, sign out!",
                    cancelButtonText: "No, return",
                    customClass: {
                        confirmButton: "btn btn-primary",
                        cancelButton: "btn btn-active-light"
                    }
                }).then(function (result) {
                    if (result.value) {
                        Swal.fire({
                            text: "You have signed out " + deviceName + "!.",
                            icon: "success",
                            buttonsStyling: false,
                            confirmButtonText: "Ok, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary",
                            }
                        }).then(function(){
                            button.closest('tr').remove();
                        });
                    } else if (result.dismiss === 'cancel') {
                        Swal.fire({
                            text: deviceName + "'s session is still preserved!.",
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
        });


    }

    // Delete two step authentication handler
    const initDeleteTwoStep = () => {
        const deleteButton = document.getElementById('kt_users_delete_two_step');

        deleteButton.addEventListener('click', e => {
            e.preventDefault();

            Swal.fire({
                text: "Are you sure you would like remove this two-step authentication?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "Yes, remove it!",
                cancelButtonText: "No, return",
                customClass: {
                    confirmButton: "btn btn-primary",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    Swal.fire({
                        text: "You have removed this two-step authentication!.",
                        icon: "success",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary",
                        }
                    });
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "Your two-step authentication is still valid!.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary",
                        }
                    });
                }
            });
        })
    }

    // Email preference form handler
    const initEmailPreferenceForm = () => {
        // Define variables
        const form = document.getElementById('kt_users_email_notification_form');
        const submitButton = form.querySelector('#kt_users_email_notification_submit');
        const cancelButton = form.querySelector('#kt_users_email_notification_cancel');

        // Submit action handler
        submitButton.addEventListener('click', e => {
            e.preventDefault();

            // Show loading indication
            submitButton.setAttribute('data-kt-indicator', 'on');

            // Disable button to avoid multiple click 
            submitButton.disabled = true;

            // Simulate form submission. For more info check the plugin's official documentation: https://sweetalert2.github.io/
            setTimeout(function () {
                // Remove loading indication
                submitButton.removeAttribute('data-kt-indicator');

                // Enable button
                submitButton.disabled = false;

                // Show popup confirmation 
                Swal.fire({
                    text: "Form has been successfully submitted!",
                    icon: "success",
                    buttonsStyling: false,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });

                //form.submit(); // Submit form
            }, 2000);
        });

        cancelButton.addEventListener('click', e => {
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
            initLoginSession();
            initSignOutUser();
            initDeleteTwoStep();
            initEmailPreferenceForm();
        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTUsersViewMain.init();
});