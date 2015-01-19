(function (){
    "use strict";

    $.ajaxSetup({
         beforeSend: function(xhr, settings) {
             function getCookie(name) {
                 var cookieValue = null
                 if (document.cookie && document.cookie !== '') {
                     var cookies = document.cookie.split(';')
                     for (var i = 0; i < cookies.length; i++) {
                         var cookie = jQuery.trim(cookies[i])
                         if (cookie.substring(0, name.length + 1) == (name + '=')) {
                             cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                             break;
                        }
                    }
                }
                return cookieValue;
             }
             if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                 xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'))
             }
         }
    })

    $('body').on('show.bs.modal', function (e) {
        $('.send_activation').on('click', sendActivation)
        $('#add_user').on('click', addUser)
    })

    var spinopts = {
        lines: 13,
        length: 20,
        width: 10,
        radius: 30,
        corners: 1,
        rotate: 0,
        direction: 1,
        color: '#000',
        speed: 1,
        trail: 60,
        shadow: false,
        hwaccel: false,
        className: 'spinner',
        zIndex: 2e9,
        top: '50%',
        left: '50%'
    };

    function addUser(evt) {
        evt.preventDefault()
        var usertable = $('#users')
        var email = $('#email').val()
        if (email === '') {
            addNotification({
                'type' : 'danger',
                'text' : 'Please enter an email address.'
            })
            return
        }
        var spinner = new Spinner(spinopts).spin(usertable.parents('.panel-body').get(0))
        $.post(
            '/user/add/',
            {email : email},
            function(data) {
                usertable.html(data)
            }
        ).done(function() {
            $('#email').val('')
            spinner.stop()
        })
    }

    function sendActivation(evt) {
        evt.preventDefault()
        var id = $(this).data('user-id')
        $.post(
            '/user/activate/send/',
            {
                'id' : id
            }
        )
    }
})();
