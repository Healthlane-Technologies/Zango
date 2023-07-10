"use strict";

// Class definition
var KTPricingGeneral = function () {
    // Private variables
    var element;
	var planPeriodMonthButton;
	var planPeriodAnnualButton;

	var changePlanPrices = function(type) {
		var items = [].slice.call(element.querySelectorAll('[data-kt-plan-price-month]'));

		items.map(function (item) {
			var monthPrice = item.getAttribute('data-kt-plan-price-month');
			var annualPrice = item.getAttribute('data-kt-plan-price-annual');

			if ( type === 'month' ) {
				item.innerHTML = monthPrice;
			} else if ( type === 'annual' ) {
				item.innerHTML = annualPrice;
			}
		});
	}

    var handlePlanPeriodSelection = function(e) {

        // Handle period change
        planPeriodMonthButton.addEventListener('click', function (e) {
            e.preventDefault();

            planPeriodMonthButton.classList.add('active');
            planPeriodAnnualButton.classList.remove('active');

            changePlanPrices('month');
        });

		planPeriodAnnualButton.addEventListener('click', function (e) {
            e.preventDefault();

            planPeriodMonthButton.classList.remove('active');
            planPeriodAnnualButton.classList.add('active');
            
            changePlanPrices('annual');
        });
    }

    // Public methods
    return {
        init: function () {
            element = document.querySelector('#kt_pricing');
			planPeriodMonthButton = element.querySelector('[data-kt-plan="month"]');
			planPeriodAnnualButton = element.querySelector('[data-kt-plan="annual"]');

            // Handlers
            handlePlanPeriodSelection();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTPricingGeneral.init();
});
