"use strict";

var KTSupportCenterGeneral = function() {
    var menuWrapper;

    var initInstance = function(element) {
        var elements = element;

        if ( typeof elements === 'undefined' ) {
            elements = document.querySelectorAll('.highlight');
        }

        if ( elements && elements.length > 0 ) {
            for ( var i = 0; i < elements.length; ++i ) {
                var highlight = elements[i];
                var copy = highlight.querySelector('.highlight-copy');

                if ( copy ) {
                    var clipboard = new ClipboardJS(copy, {
                        target: function(trigger) {
                            var highlight = trigger.closest('.highlight');
                            var el = highlight.querySelector('.tab-pane.active');

                            if ( el == null ) {
                                el = highlight.querySelector('.highlight-code');
                            }

                            return el;
                        }
                    });

                    clipboard.on('success', function(e) {
                        var caption = e.trigger.innerHTML;

                        e.trigger.innerHTML = 'copied';
                        e.clearSelection();

                        setTimeout(function() {
                            e.trigger.innerHTML = caption;
                        }, 2000);
                    });
                }
            }
        }
    }

    var handleMenuScroll = function() {
        var menuActiveItem = menuWrapper.querySelector(".menu-link.active");

        if ( !menuActiveItem ) {
            return;
        } 

        if ( KTUtil.isVisibleInContainer(menuActiveItem, menuWrapper) === true) {
            return;
        }

        menuWrapper.scroll({
            top: KTUtil.getRelativeTopPosition(menuActiveItem, menuWrapper),
            behavior: 'smooth'
        });
    }

    return {
        init: function() {
            initInstance();
        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTSupportCenterGeneral.init();
});