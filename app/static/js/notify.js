$(function() {
    "use strict";

    window.addNotification = function(options) {
        var elem = $('<div class="notification"></div>')
        $('#messages').append(elem)
        elem.notify({
            type: options.type,
            message: { html: options.text },
            fadeOut: { enabled: true, delay: 10000}
        }).show()
    }

    $('#messages .notification').each(function(){
        var type = $(this).data('notify-type');
        var text = $(this).data('notify-text');
        $(this).notify({
            type: type,
            message: { html: text },
            fadeOut: { enabled: true, delay: 10000}
        }).show()
    });

    $('#messages').on('click', '.notification', function() {
        $(this).slideUp()
    })
});
