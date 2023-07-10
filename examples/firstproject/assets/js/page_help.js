/*
*  altair admin
*  @version v2.13.0
*  @author tzd
*  @license http://themeforest.net/licenses
*  page_help.js - page_help.html
*/

$(function() {
    // help/faq
    altair_help.init();
});


altair_help  = {
    init: function() {
        // variables
        var $toggleAll_btn = $('#toggleAll'),
            $help_accordion = $('.help_accordion');


        UIkit.accordion($help_accordion, {
            collapse: false,
            showfirst: false
        });

        $toggleAll_btn.on('click', function(e) {
            e.preventDefault();
            $toggleAll_btn.velocity("transition.expandOut", {
                duration: 280,
                easing: easing_swiftOut,
                begin: function() {
                    if(!$help_accordion.hasClass('all_expanded')) {
                        $help_accordion.addClass('all_expanded').find('.uk-accordion-title').not('.uk-active').trigger('click');
                    } else {
                        $help_accordion.removeClass('all_expanded').find('.uk-accordion-title.uk-active').trigger('click');
                    }
                },
                complete: function() {
                    $toggleAll_btn.velocity("transition.expandIn", {
                        duration: 280,
                        easing: easing_swiftOut,
                        begin: function() {
                            if(!$help_accordion.hasClass('all_expanded')) {
                                $toggleAll_btn.html('&#xe8f2;');
                            } else {
                                $toggleAll_btn.html('&#xe8ee;');
                            }
                        }
                    })
                }
            });

        });
    }
};