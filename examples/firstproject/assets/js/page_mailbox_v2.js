/*
*  altair admin
*  @version v2.11.0
*  @author tzd
*  @license http://themeforest.net/licenses
*  page_mailbox_v2.js - page_mailbox_v2.html
*/

$(function() {
    // mailbox init functions
    altair_mailbox_v2.init();
});

// variables
var $mailbox = $('#mailboxV2');

altair_mailbox_v2 = {
    init: function() {
        // select messages
        altair_mailbox_v2.select_messages();
        // go to messages
        //altair_mailbox_v2.goto_message();
        // compose message
        altair_mailbox_v2.create_message();
    },
    // select messages
    select_messages: function () {
        $mailbox.on('ifChanged', '[data-md-icheck]', function() {
            $(this).is(':checked') ? $(this).closest('tr').addClass('row-selected') : $(this).closest('tr').removeClass('row-selected');
        });

        $('#mailboxV2_select_all').on('ifChanged',function() {
            var $this = $(this);
            $mailbox.find('[data-md-icheck]').each(function() {
                $this.is(':checked') ? $(this).iCheck('check') : $(this).iCheck('uncheck');
            })
        });
    },
    // go to single messages
    goto_message: function () {
        // in html data-link="page_single_message.html"
        $mailbox.on('click', 'tr[data-link]', function(e) {
            var link = $(this).attr('data-link');
            console.log(link);
        });
    },
    // compose message
    create_message: function() {

        // callback on modal show
        $('#mailbox_new_message').on('show.uk.modal',function() {});

        // file upload
        var progressbar = $("#mail_progressbar"),
            bar         = progressbar.find('.uk-progress-bar'),
            settings    = {
                action: './upload/', // upload url
                single: false,
                loadstart: function() {
                    bar.css("width", "0%").text("0%");
                    progressbar.removeClass("uk-hidden uk-progress-danger");
                },
                progress: function(percent) {
                    percent = Math.ceil(percent);
                    bar.css("width", percent+"%").text(percent+"%");
                    if(percent == '100') {
                        setTimeout(function(){
                            //progressbar.addClass("uk-hidden");
                        }, 1500);
                    }
                },
                error: function(event) {
                    progressbar.addClass("uk-progress-danger");
                    bar.css({'width':'100%'}).text('100%');
                },
                abort: function(event) {
                    console.log(event);
                },
                complete: function(response, xhr) {
                    console.log(response);
                }
            };

        var select = UIkit.uploadSelect($("#mail_upload-select"), settings),
            drop   = UIkit.uploadDrop($("#mail_upload-drop"), settings);

    }
};