"use strict";

// Class definition
var KTProfileGeneral = function () {
    // init variables
    var showMoreButton;
    var showMoreCards;
    var followBtn;
    var profileNav;
    var pageToolbar;

    // Private functions
    var handleShowMore = function () {
        if (!showMoreButton) {
            return;
        }

        // Show more click
        showMoreButton.addEventListener('click', function (e) {
            showMoreButton.setAttribute('data-kt-indicator', 'on');

            // Disable button to avoid multiple click 
            showMoreButton.disabled = true;
            
            setTimeout(function() {
                // Hide loading indication
                showMoreButton.removeAttribute('data-kt-indicator');

                // Enable button
				showMoreButton.disabled = false;

                // Hide button
                showMoreButton.classList.add('d-none');

                // Show card
                showMoreCards.classList.remove('d-none');

                // Scroll to card
                KTUtil.scrollTo(showMoreCards, 200);
            }, 2000);
        });
    }

    // Follow button
    var handleUFollow = function() {
        if (!followBtn) {
            return;
        }

        followBtn.addEventListener('click', function(e){
            // Prevent default action 
            e.preventDefault();
            
            // Show indicator
            followBtn.setAttribute('data-kt-indicator', 'on');
            
            // Disable button to avoid multiple click 
            followBtn.disabled = true;

            // Check button state
            if (followBtn.classList.contains("btn-success")) {
                    setTimeout(function() {
                    followBtn.removeAttribute('data-kt-indicator');
                    followBtn.classList.remove("btn-success");
                    followBtn.classList.add("btn-light");
                    followBtn.querySelector("i").classList.add("d-none");
                    followBtn.querySelector(".indicator-label").innerHTML = 'Follow';
                    followBtn.disabled = false;
                }, 1500);   
            } else {
                    setTimeout(function() {
                    followBtn.removeAttribute('data-kt-indicator');
                    followBtn.classList.add("btn-success");
                    followBtn.classList.remove("btn-light");
                    followBtn.querySelector("i").classList.remove("d-none");
                    followBtn.querySelector(".indicator-label").innerHTML = 'Following';
                    followBtn.disabled = false;
                }, 1000);   
            }        
        });        
    }

    var handleFollowers = function() {
        KTUtil.on(document.body,  '[data-kt-follow-btn="true"]', 'click', function(e) {
            e.preventDefault();

            var el = this;
            var label = el.querySelector(".indicator-label");
            var following = el.querySelector(".following");
            var follow = el.querySelector(".follow");

            el.setAttribute('data-kt-indicator', 'on');            
            el.disabled = true;
            follow.classList.add("d-none");
            following.classList.add("d-none")

            setTimeout(function() {
                el.removeAttribute('data-kt-indicator');
				el.disabled = false;

                if (el.classList.contains("btn-light-primary")) { // following
                    el.classList.remove("btn-light-primary");
                    el.classList.add("btn-light");

                    follow.classList.remove("d-none");

                    label.innerHTML = "Follow";
                } else {  // follow
                    el.classList.add("btn-light-primary");
                    el.classList.remove("btn-light");

                    following.classList.remove("d-none");

                    label.innerHTML = "Following";
                }
            }, 2000);
        });
    }

    var handlePageScroll = function() {
        if ( profileNav  && profileNav.getAttribute("data-kt-sticky") && KTUtil.isBreakpointUp('lg')) {
            
            if ( localStorage.getItem('nav-initialized') === "1") {
                window.scroll({
                    top: parseInt(profileNav.getAttribute("data-kt-page-scroll-position")),
                    behavior: 'smooth'
                });
            }
    
            localStorage.setItem('nav-initialized', "1");        
        }        
    }

    // Public methods
    return {
        init: function () {
            showMoreButton = document.querySelector('#kt_followers_show_more_button');
            showMoreCards = document.querySelector('#kt_followers_show_more_cards');
            followBtn = document.querySelector('#kt_user_follow_button');
            profileNav = document.querySelector('#kt_user_profile_nav');

            handleShowMore();
            handleUFollow();
            handleFollowers();
            handlePageScroll();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTProfileGeneral.init();
});