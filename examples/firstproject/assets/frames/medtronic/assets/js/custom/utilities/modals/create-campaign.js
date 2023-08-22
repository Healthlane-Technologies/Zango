"use strict";

// Class definition
var KTCreateCampaign = function () {
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
		// Init age slider
		var slider = document.querySelector("#kt_modal_create_campaign_age_slider");
		var valueMin = document.querySelector("#kt_modal_create_campaign_age_min");
		var valueMax = document.querySelector("#kt_modal_create_campaign_age_max");

		noUiSlider.create(slider, {
			start: [18, 40],
			connect: true,
			range: {
				"min": 13,
				"max": 80
			}
		});

		slider.noUiSlider.on("update", function (values, handle) {
			if (handle) {
				valueMax.innerHTML = Math.round(values[handle]);
			} else {
				valueMin.innerHTML = Math.round(values[handle]);
			}
		});

		// Init tagify
		var tagifyElement = document.querySelector('#kt_modal_create_campaign_location');
		var tagify = new Tagify(tagifyElement, {
			delimiters: null,
			templates: {
				tag: function (tagData) {
					const countryPath = tagifyElement.getAttribute("data-kt-flags-path") + tagData.value.toLowerCase().replace(/\s+/g, '-') + '.svg';
					try {
						// _ESCAPE_START_
						return `<tag title='${tagData.value}' contenteditable='false' spellcheck="false" class='tagify__tag ${tagData.class ? tagData.class : ""}' ${this.getAttributes(tagData)}>
                                <x title='remove tag' class='tagify__tag__removeBtn'></x>
                                <div class="d-flex align-items-center">
                                    ${tagData.code ?
								`<img onerror="this.style.visibility = 'hidden'" class="w-25px rounded-circle me-2" src='${countryPath}' />` : ''
							}
                                    <span class='tagify__tag-text'>${tagData.value}</span>
                                </div>
                            </tag>`
						// _ESCAPE_END_
					}
					catch (err) { }
				},

				dropdownItem: function (tagData) {
					const countryPath = tagifyElement.getAttribute("data-kt-flags-path") + tagData.value.toLowerCase().replace(/\s+/g, '-') + '.svg';
					try {
						// _ESCAPE_START_
						return `<div class='tagify__dropdown__item ${tagData.class ? tagData.class : ""}'>
                                    <img onerror="this.style.visibility = 'hidden'" class="w-25px rounded-circle me-2"
                                         src='${countryPath}' />
                                    <span>${tagData.value}</span>
                                </div>`
						// _ESCAPE_END_
					}
					catch (err) { }
				}
			},
			enforceWhitelist: true,
			whitelist: [
				{ value: 'Argentina', code: 'AR' },
				{ value: 'Australia', code: 'AU', searchBy: 'beach, sub-tropical' },
				{ value: 'Austria', code: 'AT' },
				{ value: 'Brazil', code: 'BR' },
				{ value: 'China', code: 'CN' },
				{ value: 'Egypt', code: 'EG' },
				{ value: 'Finland', code: 'FI' },
				{ value: 'France', code: 'FR' },
				{ value: 'Germany', code: 'DE' },
				{ value: 'Hong Kong', code: 'HK' },
				{ value: 'Hungary', code: 'HU' },
				{ value: 'Iceland', code: 'IS' },
				{ value: 'India', code: 'IN' },
				{ value: 'Indonesia', code: 'ID' },
				{ value: 'Italy', code: 'IT' },
				{ value: 'Jamaica', code: 'JM' },
				{ value: 'Japan', code: 'JP' },
				{ value: 'Jersey', code: 'JE' },
				{ value: 'Luxembourg', code: 'LU' },
				{ value: 'Mexico', code: 'MX' },
				{ value: 'Netherlands', code: 'NL' },
				{ value: 'New Zealand', code: 'NZ' },
				{ value: 'Norway', code: 'NO' },
				{ value: 'Philippines', code: 'PH' },
				{ value: 'Singapore', code: 'SG' },
				{ value: 'South Korea', code: 'KR' },
				{ value: 'Sweden', code: 'SE' },
				{ value: 'Switzerland', code: 'CH' },
				{ value: 'Thailand', code: 'TH' },
				{ value: 'Ukraine', code: 'UA' },
				{ value: 'United Kingdom', code: 'GB' },
				{ value: 'United States', code: 'US' },
				{ value: 'Vietnam', code: 'VN' }
			],
			dropdown: {
				enabled: 1, // suggest tags after a single character input
				classname: 'extra-properties' // custom class for the suggestions dropdown
			} // map tags' values to this property name, so this property will be the actual value and not the printed value on the screen
		})

		// add the first 2 tags and makes them readonly
		var tagsToAdd = tagify.settings.whitelist.slice(0, 2);
		tagify.addTags(tagsToAdd);

		// Init flatpickr
		$("#kt_modal_create_campaign_datepicker").flatpickr({
			altInput: true,
			enableTime: true,
			altFormat: "F j, Y H:i",
			dateFormat: "Y-m-d H:i",
			mode: "range"
		});

		// Init dropzone
		var myDropzone = new Dropzone("#kt_modal_create_campaign_files_upload", {
			url: "https://keenthemes.com/scripts/void.php", // Set the url for your upload script location
			paramName: "file", // The name that will be used to transfer the file
			maxFiles: 10,
			maxFilesize: 10, // MB
			addRemoveLinks: true,
			accept: function(file, done) {
				if (file.name == "wow.jpg") {
					done("Naha, you don't.");
				} else {
					done();
				}
			}
		});

		// Handle campaign duration options
		const allDuration = document.querySelector('#kt_modal_create_campaign_duration_all');
		const fixedDuration = document.querySelector('#kt_modal_create_campaign_duration_fixed');
		const datepicker = document.querySelector('#kt_modal_create_campaign_datepicker');

		[allDuration, fixedDuration].forEach(option => {
			option.addEventListener('click', e => {
				if (option.classList.contains('active')) {
					return;
				}
				allDuration.classList.toggle('active');
				fixedDuration.classList.toggle('active');

				if (fixedDuration.classList.contains('active')) {
					datepicker.nextElementSibling.classList.remove('d-none');
				} else {
					datepicker.nextElementSibling.classList.add('d-none');
				}
			});
		});

		// Init budget slider
		var budgetSlider = document.querySelector("#kt_modal_create_campaign_budget_slider");
		var budgetValue = document.querySelector("#kt_modal_create_campaign_budget_label");

		noUiSlider.create(budgetSlider, {
			start: [5],
			connect: true,
			range: {
				"min": 1,
				"max": 500
			}
		});

		budgetSlider.noUiSlider.on("update", function (values, handle) {
			budgetValue.innerHTML = Math.round(values[handle]);
			if (handle) {
				budgetValue.innerHTML = Math.round(values[handle]);
			}
		});

		// Handle create new campaign button
		const restartButton = document.querySelector('#kt_modal_create_campaign_create_new');
		restartButton.addEventListener('click', function () {
			form.reset();
			stepperObj.goTo(1);
		});
	}

	var initValidation = function () {
		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		// Step 1
		validations.push(FormValidation.formValidation(
			form,
			{
				fields: {
					campaign_name: {
						validators: {
							notEmpty: {
								message: 'App name is required'
							}
						}
					},
					avatar: {
						validators: {
							file: {
								extension: 'png,jpg,jpeg',
								type: 'image/jpeg,image/png',
								message: 'Please choose a png, jpg or jpeg files only',
							},
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

	return {
		// Public Functions
		init: function () {
			// Elements
			modalEl = document.querySelector('#kt_modal_create_campaign');

			if (!modalEl) {
				return;
			}

			modal = new bootstrap.Modal(modalEl);

			stepper = document.querySelector('#kt_modal_create_campaign_stepper');
			form = document.querySelector('#kt_modal_create_campaign_stepper_form');
			formSubmitButton = stepper.querySelector('[data-kt-stepper-action="submit"]');
			formContinueButton = stepper.querySelector('[data-kt-stepper-action="next"]');

			initStepper();
			initForm();
			initValidation();
		}
	};
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
	KTCreateCampaign.init();
});
