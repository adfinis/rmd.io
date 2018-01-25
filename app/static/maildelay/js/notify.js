$(function() {

    window.addNotification = function(options) {
        var icons = {
            'danger'  : 'bolt',
            'warning' : 'warning',
            'info'    : 'info-circle',
            'success' : 'check'
        }
        var prefixes = {
            'danger'  : 'Error',
            'warning' : 'Warning',
            'info'    : 'Info',
            'success' : 'Success'
        }

        var elem = $('<div class="notification"></div>')
        $('#messages').append(elem)

        var prefix = '<strong> '+prefixes[options.type]+'!</strong> '
        var icon   = '<i class="fa fa-'+icons[options.type]+'"></i>'
        elem.notify({
            type: options.type,
            message: { html: icon + prefix + options.text },
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
