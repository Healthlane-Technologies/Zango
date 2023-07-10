/*
*  altair admin
*  @version v2.11.0
*  @author tzd
*  @license http://themeforest.net/licenses
*  components_notifications.js - components_notifications.html
*/

// custom callback
function notify_callback() {
    return alert('Notify closed!');
}

function executeCallback(callback) {
    window[callback]();
}

function showNotify($element) {
    thisNotify = UIkit.notify({
        message: $element.data('message') ? $element.data('message') : '',
        status: $element.data('status') ? $element.data('status') : '',
        timeout: $element.attr('data-timeout') ? $element.data('timeout') : 5000,
        group: $element.data('group') ? $element.data('group') : null,
        pos: $element.data('pos') ? $element.data('pos') : 'top-center',
        onClose: function() {
            $body.find('.md-fab-wrapper').css('margin-bottom','');
            if($element.data('callback')) {
                executeCallback($element.data('callback'));
            }
            // clear notify timeout (sometimes callback is fired more than once)
            clearTimeout(thisNotify.timeout)
        }
    });
    if(
        (
            ($window.width() < 768)
            && (
                (thisNotify.options.pos == 'bottom-right')
                || (thisNotify.options.pos == 'bottom-left')
                || (thisNotify.options.pos == 'bottom-center')
            )
        )
        || (thisNotify.options.pos == 'bottom-right')
    ) {
        var thisNotify_height = $(thisNotify.element).outerHeight();
        var spacer = $window.width() < 768 ? -6 : 8;
        $body.find('.md-fab-wrapper').css('margin-bottom',thisNotify_height + spacer);
    }
}

$(function() {
    // notifications
    altair_notifications.init();
});

altair_notifications = {
    init: function() {

        $body.on("click", "[data-message]", function(){
            var $this = $(this);
            if($body.find('.uk-notify-message').length) {
                $body.find('.uk-notify-message').click();
                setTimeout(function() {
                    showNotify($this)
                },450)
            } else {
                showNotify($this)
            }
        });

    }
};