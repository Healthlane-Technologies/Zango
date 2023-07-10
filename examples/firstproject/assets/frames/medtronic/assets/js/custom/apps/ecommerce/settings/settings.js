"use strict";

// Class definition
var KTAppEcommerceSettings = function () {
    // Shared variables


    // Private functions
    const initForms = () => {
        const forms = [
            'kt_ecommerce_settings_general_form',
            'kt_ecommerce_settings_general_store',
            'kt_ecommerce_settings_general_localization',
            'kt_ecommerce_settings_general_products',
            'kt_ecommerce_settings_general_customers',
        ];

        // Init all forms
        forms.forEach(formId => {
            // Select form
            const form = document.getElementById(formId);

            if(!form){
                return;
            }

            // Dynamically create validation non-empty rule
            const requiredFields = form.querySelectorAll('.required');
            var detectedField;
            var validationFields = {
                fields: {},

                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }

            // Detect required fields
            requiredFields.forEach(el => {
                const input = el.closest('.row').querySelector('input');
                if (input) {
                    detectedField = input;
                }

                const textarea = el.closest('.row').querySelector('textarea');
                if (textarea) {
                    detectedField = textarea;
                }

                const select = el.closest('.row').querySelector('select');
                if (select) {
                    detectedField = select;
                }

                // Add validation rule                
                const name = detectedField.getAttribute('name');
                validationFields.fields[name] = {
                    validators: {
                        notEmpty: {
                            message: el.innerText + ' is required'
                        }
                    }
                }
            });

            // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
            var validator = FormValidation.formValidation(
                form,
                validationFields
            );

            // Submit button handler
            const submitButton = form.querySelector('[data-kt-ecommerce-settings-type="submit"]');
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
                        } else {
                            // Show popup error 
                            Swal.fire({
                                text: "Oops! There are some error(s) detected.",
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
        });
    }

    // Init Tagify
    const initTagify = () => {
        // Get tagify elements
        const elements = document.querySelectorAll('[data-kt-ecommerce-settings-type="tagify"]');

        // Init tagify
        elements.forEach(element => {
            new Tagify(element);
        });
    }

    // Init Select2 with flags
    const initSelect2Flags = () => {
        // Format options
        const optionFormat = (item) => {
            if ( !item.id ) {
                return item.text;
            }

            var span = document.createElement('span');
            var template = '';

            template += '<img src="' + item.element.getAttribute('data-kt-select2-country') + '" class="rounded-circle h-20px me-2" alt="image"/>';
            template += item.text;

            span.innerHTML = template;

            return $(span);
        }

        // Init Select2 --- more info: https://select2.org/
        $('[data-kt-ecommerce-settings-type="select2_flags"]').select2({
            placeholder: "Select a country",
            minimumResultsForSearch: Infinity,
            templateSelection: optionFormat,
            templateResult: optionFormat
        });
    }

    // Public methods
    return {
        init: function () {

            initForms();
            initTagify();
            initSelect2Flags();

        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTAppEcommerceSettings.init();
});
