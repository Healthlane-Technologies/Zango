"use strict";

// Class definition
var KTContactApply = function () {
	var submitButton;
	var validator;
	var form;
	var selectedlocation;

	// Private functions
    var initMap = function(elementId) {
        // Check if Leaflet is included
        if (!L) {
            return;
        }

        // Define Map Location
        var leaflet = L.map(elementId, {
            center: [40.725, -73.985],
            zoom: 30
        });

        // Init Leaflet Map. For more info check the plugin's documentation: https://leafletjs.com/
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(leaflet);

        // Set Geocoding
        var geocodeService;
        if (typeof L.esri.Geocoding === 'undefined') {
            geocodeService = L.esri.geocodeService();
        } else {
            geocodeService = L.esri.Geocoding.geocodeService();
        }

        // Define Marker Layer
        var markerLayer = L.layerGroup().addTo(leaflet);

        // Set Custom SVG icon marker
        var leafletIcon = L.divIcon({
            html: `<i class="ki-solid ki-geolocation text-primary fs-3x"></span>`,
            bgPos: [10, 10],
            iconAnchor: [20, 37],
            popupAnchor: [0, -37],
            className: 'leaflet-marker'
        });

		// Show current address
		L.marker([40.724716, -73.984789], { icon: leafletIcon }).addTo(markerLayer).bindPopup('430 E 6th St, New York, 10009.', { closeButton: false }).openPopup();

        // Map onClick Action
        leaflet.on('click', function (e) {
            geocodeService.reverse().latlng(e.latlng).run(function (error, result) {
                if (error) {
                    return;
                }
                markerLayer.clearLayers();
                selectedlocation = result.address.Match_addr;
                L.marker(result.latlng, { icon: leafletIcon }).addTo(markerLayer).bindPopup(result.address.Match_addr, { closeButton: false }).openPopup();

                // Show popup confirmation. For more info check the plugin's official documentation: https://sweetalert2.github.io/
                Swal.fire({
                    html: 'Your selected - <b>"' + selectedlocation + ' - ' + result.latlng + '"</b>.',
                    icon: "success",
                    buttonsStyling: false,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                }).then(function (result) {
                    // Confirmed
                });
            });
        });
    }

	// Init form inputs
	var initForm = function() {
		// Team assign. For more info, plase visit the official plugin site: https://select2.org/
        $(form.querySelector('[name="position"]')).on('change', function() {
            // Revalidate the field when an option is chosen
            validator.revalidateField('position');
        });		
	}

	// Handle form validation and submittion
	var handleForm = function() {
		// Stepper custom navigation

		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		validator = FormValidation.formValidation(
			form,
			{
				fields: {
					'name': {
						validators: {
							notEmpty: {
								message: 'Name is required'
							}
						}
					},
					'email': {
                        validators: {
							notEmpty: {
								message: 'Email address is required'
							},
                            emailAddress: {
								message: 'The value is not a valid email address'
							}
						}
					},
					'message': {
                        validators: {
							notEmpty: {
								message: 'Message is required'
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

		// Action buttons
		submitButton.addEventListener('click', function (e) {
			e.preventDefault();

			// Validate form before submit
			if (validator) {
				validator.validate().then(function (status) {
					console.log('validated!');

					if (status == 'Valid') {
						submitButton.setAttribute('data-kt-indicator', 'on');

						// Disable button to avoid multiple click 
						submitButton.disabled = true;

						setTimeout(function() {
							submitButton.removeAttribute('data-kt-indicator');

							// Enable button
							submitButton.disabled = false;
							
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
									//form.submit();
								}
							});

							//form.submit(); // Submit form
						}, 2000);   						
					} else {
						// Scroll top

						// Show error popuo. For more info check the plugin's official documentation: https://sweetalert2.github.io/
						Swal.fire({
							text: "Sorry, looks like there are some errors detected, please try again.",
							icon: "error",
							buttonsStyling: false,
							confirmButtonText: "Ok, got it!",
							customClass: {
								confirmButton: "btn btn-primary"
							}
						}).then(function (result) {
							KTUtil.scrollTop();
						});
					}
				});
			}
		});
	}

	return {
		// Public functions
		init: function () {
			// Elements
			form = document.querySelector('#kt_contact_form');
			submitButton = document.getElementById('kt_contact_submit_button');

			initForm();
			handleForm();
			initMap('kt_contact_map');
		}
	};
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
	KTContactApply.init();
});