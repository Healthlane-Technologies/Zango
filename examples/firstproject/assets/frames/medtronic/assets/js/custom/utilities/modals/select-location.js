"use strict";

// Class definition
var KTModalSelectLocation = function () {
    // Private variables
    var locationSelectTarget;
    var locationSelectButton;

    var modal;
    var selectedlocation = '';
    var mapInitialized = false;

    // Private functions
    var initMap = function() {
        // Check if Leaflet is included
        if (!L) {
            return;
        }

        // Define Map Location
        var leaflet = L.map('kt_modal_select_location_map', {
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
                    html: '<div class="mb-2">Your selected - <b>"' + selectedlocation + '"</b>.</div>' + 'Click on the "Apply" button to select this location.',
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

    var handleSelection = function() {
        locationSelectButton.addEventListener('click', function() {
            if (locationSelectTarget) {
                if (locationSelectTarget.value) {
                    locationSelectTarget.value = selectedlocation;
                } else {
                    locationSelectTarget.innerHTML = selectedlocation;
                }
            }
        });
    }

    // Public methods
    return {
        init: function () {
            // Elements
			modal = document.querySelector('#kt_modal_select_location');

			if (!modal) {
				return;
			}
            
            locationSelectTarget = document.querySelector('#kt_modal_select_location_target');
            locationSelectButton = document.querySelector('#kt_modal_select_location_button');

            handleSelection();
            
            modal.addEventListener('shown.bs.modal', function () {
                if (!mapInitialized) {
                    initMap();
                    mapInitialized = true;
                }                
            });
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTModalSelectLocation.init();
});
