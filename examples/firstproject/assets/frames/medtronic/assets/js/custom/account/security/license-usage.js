"use strict";

// Class definition
var KTAccountSecurityLicenseUsage = function () {
    // Private functions
    var initLicenceCopy = function() {
        KTUtil.each(document.querySelectorAll('#kt_security_license_usage_table [data-action="copy"]'), function(button) {
            var tr = button.closest('tr');
            var license = KTUtil.find(tr, '[data-bs-target="license"]');

            var clipboard = new ClipboardJS(button, {
                target: license,
                text: function() {
                    return license.innerHTML;
                }
            });
        
            clipboard.on('success', function(e) {
                // Icons
                var copyIcon = button.querySelector('.ki-copy');                
                var checkIcon = button.querySelector('.ki-check');
                
                // exit if check icon is already shown
                if (checkIcon) {
                   return;  
                }

                // Create check icon
                checkIcon = document.createElement('i');
                checkIcon.classList.add('ki-solid');
                checkIcon.classList.add('ki-check');
                checkIcon.classList.add('fs-2');

                // Append check icon
                button.appendChild(checkIcon);

                // Highlight target
                license.classList.add('text-success');

                // Hide copy icon
                copyIcon.classList.add('d-none');

                // Set 3 seconds timeout to hide the check icon and show copy icon back
                setTimeout(function() {
                    // Remove check icon
                    copyIcon.classList.remove('d-none');
                    // Show check icon back
                    button.removeChild(checkIcon);

                    // Remove highlight
                    license.classList.remove('text-success');
                }, 3000);
            });
        });
    }

    // Public methods
    return {
        init: function () {
            initLicenceCopy();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTAccountSecurityLicenseUsage.init();
});
