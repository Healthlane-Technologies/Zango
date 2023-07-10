"use strict";
 
// Class definition
var KTSearchHorizontal = function () {
    // Private functions
    var initAdvancedSearchForm = function () {
       var form = document.querySelector('#kt_advanced_search_form');

       // Init tags
       var tags = form.querySelector('[name="tags"]');
       new Tagify(tags);
    }

    var handleAdvancedSearchToggle = function () {
        var link = document.querySelector('#kt_horizontal_search_advanced_link');

        link.addEventListener('click', function (e) {
            e.preventDefault();
            
            if (link.innerHTML === "Advanced Search") {
                link.innerHTML = "Hide Advanced Search";
            } else {
                link.innerHTML = "Advanced Search";
            }
        })
    }

    // Public methods
    return {
        init: function () {
            initAdvancedSearchForm();
            handleAdvancedSearchToggle();
        }
    }     
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTSearchHorizontal.init();
});
