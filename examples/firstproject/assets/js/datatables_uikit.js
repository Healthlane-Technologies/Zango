/*!
* DataTables UIKit integration
* author: tzd
*/

(function(window, document, undefined){

    var factory = function( $, DataTable ) {
        "use strict";


        /* Set the defaults for DataTables initialisation */
        $.extend( true, DataTable.defaults, {
            dom:
            "<'dt-uikit-header'<'uk-grid'<'uk-width-medium-2-3'l><'uk-width-medium-1-3'f>>>" +
            "<'uk-overflow-container'tr>" +
            "<'dt-uikit-footer'<'uk-grid'<'uk-width-medium-3-10'i><'uk-width-medium-7-10'p>>>",
            renderer: 'uikit',
            "order": []
        } );


        /* Default class modification */
        $.extend( DataTable.ext.classes, {
            sWrapper:      "dataTables_wrapper form-inline dt-uikit",
            sFilterInput:  "md-input",
            sLengthSelect: "dt-selectize",
            "sPaging":     ""
        } );

        /* Bootstrap paging button renderer */
        DataTable.ext.renderer.pageButton.uikit = function ( settings, host, idx, buttons, page, pages ) {
            var api     = new DataTable.Api( settings );
            var classes = settings.oClasses;
            var lang    = settings.oLanguage.oPaginate;
            var btnDisplay, btnClass, counter=0;

            var attach = function( container, buttons ) {
                var i, ien, node, button;
                var clickHandler = function ( e ) {
                    e.preventDefault();
                    if ( !$(e.currentTarget).hasClass('disabled') ) {
                        api.page( e.data.action ).draw( false );
                    }
                };

                for ( i=0, ien=buttons.length ; i<ien ; i++ ) {
                    button = buttons[i];

                    if ( $.isArray( button ) ) {
                        attach( container, button );
                    }
                    else {
                        btnDisplay = '';
                        btnClass = '';

                        switch ( button ) {
                            case 'ellipsis':
                                btnDisplay = '&hellip;';
                                btnClass = 'uk-disabled';
                                break;

                            case 'first':
                                btnDisplay = '<i class="uk-icon-angle-double-left"/>';
                                btnClass = button + (page > 0 ?
                                    '' : ' uk-disabled');
                                break;

                            case 'previous':
                                btnDisplay = lang.sPrevious;
                                btnClass = button + (page > 0 ?
                                    '' : ' uk-disabled');
                                break;

                            case 'next':
                                btnDisplay = lang.sNext;
                                btnClass = button + (page < pages-1 ?
                                    '' : ' uk-disabled');
                                break;

                            case 'last':
                                btnDisplay = '<i class="uk-icon-angle-double-right"/>';
                                btnClass = button + (page < pages-1 ?
                                    '' : ' uk-disabled');
                                break;

                            default:
                                btnDisplay = button + 1;
                                btnClass = page === button ?
                                    'uk-active' : '';
                                break;
                        }

                        if ( btnDisplay ) {
                            node = $('<li>', {
                                'class': classes.sPageButton+' '+btnClass,
                                'id': idx === 0 && typeof button === 'string' ?
                                settings.sTableId +'_'+ button :
                                    null
                            } )
                                .append( $('<a>', {
                                    'href': '#',
                                    'aria-controls': settings.sTableId,
                                    'data-dt-idx': counter,
                                    'tabindex': settings.iTabIndex
                                } )
                                    .html( btnDisplay )
                            )
                                .appendTo( container );

                            settings.oApi._fnBindAction(
                                node, {action: button}, clickHandler
                            );

                            counter++;
                        }
                    }
                }
            };

            var activeEl;

            try {
                activeEl = $(document.activeElement).data('dt-idx');
            }
            catch (e) {}

            attach(
                $(host).empty().html('<ul class="uk-pagination"/>').children('ul'),
                buttons
            );

            if ( activeEl ) {
                $(host).find( '[data-dt-idx='+activeEl+']' ).focus();
            }
        };


        /*
         * TableTools uikit compatibility
        */
        if ( DataTable.TableTools ) {
            $.extend( true, DataTable.TableTools.classes, {
                "container": "DTTT uk-text-right",
                "buttons": {
                    "normal": "md-btn DTTT_btn",
                    "disabled": "md-btn-disabled"
                },
                "collection": {
                    "container": "DTTT_dropdown dropdown-menu",
                    "buttons": {
                        "normal": "",
                        "disabled": "disabled"
                    }
                },
                "print": {
                    "info": "DTTT_print_info"
                },
                "select": {
                    "row": "active"
                }
            } );

            // Have the collection use a uikit compatible drop down
            $.extend( true, DataTable.TableTools.DEFAULTS.oTags, {
                "collection": {
                    "container": "ul",
                    "button": "li",
                    "liner": "a"
                }
            } );
        }


    };

    $('body').on( 'init.dt', '.dt-uikit', function () {

            if(!$(this).hasClass('md-processed')) {
                var dt_filter = $(this).find('.dataTables_filter'),
                    search_label = dt_filter.children('label').text();

                dt_filter.find('.md-input').attr('placeholder',search_label).unwrap();

                dt_filter.contents().filter(function(){
                    return (this.nodeType == 3);
                }).remove();

                // reinitialize md inputs
                altair_md.inputs();

                // initilaize selectize
                $(this).find('.dt-selectize').selectize({
                    dropdownParent: 'body',
                    onDropdownOpen: function($dropdown) {
                        $dropdown
                            .hide()
                            .velocity('slideDown', {
                                duration: 200,
                                easing: easing_swiftOut
                            })
                    },
                    onDropdownClose: function($dropdown) {
                        $dropdown
                            .show()
                            .velocity('slideUp', {
                                duration: 200,
                                easing: easing_swiftOut
                            })
                    }
                });

                $(this).find('.ColVis_MasterButton').addClass('md-btn');

                $(this).addClass('md-processed');
            }

    });


// Define as an AMD module if possible
    if ( typeof define === 'function' && define.amd ) {
        define( ['jquery', 'datatables'], factory );
    }
    else if ( typeof exports === 'object' ) {
        // Node/CommonJS
        factory( require('jquery'), require('datatables') );
    }
    else if ( jQuery ) {
        // Otherwise simply initialise as normal, stopping multiple evaluation
        factory( jQuery, jQuery.fn.dataTable );
    }


})(window, document);