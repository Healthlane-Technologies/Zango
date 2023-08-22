"use strict";

// Class definition
var KTAppContactView = function () {
    // Private functions
    const handleDeleteButton = () => {
        // Select form
        const deleteButton = document.getElementById('kt_contact_delete');

        if (!deleteButton) {
            return;
        }

        deleteButton.addEventListener('click', e => {
            // Prevent default button action
            e.preventDefault();

            // Show popup confirmation 
            Swal.fire({
                text: "Delete contact confirmation",
                icon: "warning",
                buttonsStyling: false,
                showCancelButton: true,
                confirmButtonText: "Yes, delete it!",
                cancelButtonText: "No, return",
                customClass: {
                    confirmButton: "btn btn-danger",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    Swal.fire({
                        text: "Contact has been deleted!",
                        icon: "success",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary"
                        }
                    }).then(function (result) {
                        if (result.value) {
                            // Redirect to customers list page
                            window.location = deleteButton.getAttribute("data-kt-redirect");
                        }
                    });
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "Contact has not been deleted!.",
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

    // Public methods
    return {
        init: function () {

            handleDeleteButton();

        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTAppContactView.init();
});
