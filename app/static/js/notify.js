$(function() {
    "use strict";

    $('.notification').each(function(){
        var type = $(this).data('notify-type');
        var text = $(this).data('notify-text');
        $(this).notify({
            type: type,
            message: { html: text },
            fadeOut: { enabled: true, delay: 5000}
        }).show();
    });
});
