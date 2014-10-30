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
        $('.delete_user').on('click', deleteUser)
        $('.send_activation').on('click', sendActivation)
        $('#add_user').on('click', addUser)
    })

    function deleteUser(evt) {
        evt.preventDefault()
        var row = $(evt.target).closest('tr')
        var id = $(evt.target).closest('a').data('user-id')
        $.post(
            '/user/delete/',
            {id : id}
        ).done(
            row.hide('slow')
        )
    }

    function addUser(evt) {
        evt.preventDefault()
        var email = $('#email').val()
        $.post(
            '/user/add/',
            {email : email},
            function(data) {
                $('#users').html(data)
            }
        ).done(
            $('#email').val('')
        )
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
