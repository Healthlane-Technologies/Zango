"use strict";

// Class definition
var KTModalOfferADeal = function () {
    // Private variables
	var stepper;
	var stepperObj;
	var form;	

	// Private functions
	var initStepper = function () {
		// Initialize Stepper
		stepperObj = new KTStepper(stepper);
	}

	return {
		// Public functions
		init: function () {
			stepper = document.querySelector('#kt_modal_offer_a_deal_stepper');
			form = document.querySelector('#kt_modal_offer_a_deal_form');

			initStepper();
		},

		getStepper: function () {
			return stepper;
		},

		getStepperObj: function () {
			return stepperObj;
		},
		
		getForm: function () {
			return form;
		}
	};
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
	if (!document.querySelector('#kt_modal_offer_a_deal')) {
		return;
	}

    KTModalOfferADeal.init();
    KTModalOfferADealType.init();
    KTModalOfferADealDetails.init();
    KTModalOfferADealFinance.init();
    KTModalOfferADealComplete.init();
});

// Webpack support
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
	window.KTModalOfferADeal = module.exports = KTModalOfferADeal;
}