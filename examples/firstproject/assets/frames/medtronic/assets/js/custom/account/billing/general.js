"use strict";

// Class definition
var KTAccountBillingGeneral = function () {
    // Private variables
    var cancelSubscriptionButton;

    // Private functions
    var handlePlan = function () {
        cancelSubscriptionButton.addEventListener('click', function (e) {
            e.preventDefault();

            swal.fire({
                text: "Are you sure you would like to cancel your subscription ?",
                icon: "warning",
                buttonsStyling: false,
                showDenyButton: true,
                confirmButtonText: "Yes",
                denyButtonText: 'No',
                customClass: {
                    confirmButton: "btn btn-primary",
                    denyButton: "btn btn-light-danger"
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    Swal.fire({
                        text: 'Your subscription has been canceled.', 
                        icon: 'success',
                        confirmButtonText: "Ok",
                        buttonsStyling: false,
                        customClass: {
                            confirmButton: "btn btn-light-primary"
                        }
                    })
                } 
            });
        });
    }

    var handleCardDelete = function() {
        KTUtil.on(document.body,  '[data-kt-billing-action="card-delete"]', 'click', function(e) {
            e.preventDefault();

            var el = this;

            swal.fire({
                text: "Are you sure you would like to delete selected card ?",
                icon: "warning",
                buttonsStyling: false,
                showDenyButton: true,
                confirmButtonText: "Yes",
                denyButtonText: 'No',
                customClass: {
                    confirmButton: "btn btn-primary",
                    denyButton: "btn btn-light-danger"
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    el.setAttribute('data-kt-indicator', 'on');            
                    el.disabled = true;

                    setTimeout(function() {
                        Swal.fire({
                            text: 'Your selected card has been successfully deleted', 
                            icon: 'success',
                            confirmButtonText: "Ok",
                            buttonsStyling: false,
                            customClass: {
                                confirmButton: "btn btn-light-primary"
                            }
                        }).then((result) => {
                            el.closest('[data-kt-billing-element="card"]').remove();
                        });
                    }, 2000);
                } 
            });   
        });
    } 

    var handleAddressDelete = function() {
        KTUtil.on(document.body,  '[data-kt-billing-action="address-delete"]', 'click', function(e) {
            e.preventDefault();

            var el = this;

            swal.fire({
                text: "Are you sure you would like to delete selected address ?",
                icon: "warning",
                buttonsStyling: false,
                showDenyButton: true,
                confirmButtonText: "Yes",
                denyButtonText: 'No',
                customClass: {
                    confirmButton: "btn btn-primary",
                    denyButton: "btn btn-light-danger"
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    el.setAttribute('data-kt-indicator', 'on');            
                    el.disabled = true;

                    setTimeout(function() {
                        Swal.fire({
                            text: 'Your selected address has been successfully deleted', 
                            icon: 'success',
                            confirmButtonText: "Ok",
                            buttonsStyling: false,
                            customClass: {
                                confirmButton: "btn btn-light-primary"
                            }
                        }).then((result) => {
                            el.closest('[data-kt-billing-element="address"]').remove();
                        });
                    }, 2000);
                } 
            });   
        });
    }

    // Public methods
    return {
        init: function () {            
            cancelSubscriptionButton = document.querySelector('#kt_account_billing_cancel_subscription_btn');

            if ( cancelSubscriptionButton ) {
                handlePlan();
            }            

            handleCardDelete();
            handleAddressDelete();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTAccountBillingGeneral.init();
});
