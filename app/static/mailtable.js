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
         },
         error: function() {
            var error_popup = $('#error_popup')
            error_popup.show()
            error_popup.modal()
         }
    })

    function ajaxPopup(name) {
        return function(evt) {
            evt.preventDefault()
            var popup = $('#'+name+'_popup')
            if(popup.length === 0) {
                $('body').append('<div id="'+name+'_popup" class="modal fade" role="dialog"/>')
                popup = $('#'+name+'_popup')
                if (name === 'settings') {
                    $('#settings_popup').on('click', '.delete-address', deleteAddress)
                    $('#settings_popup').on('click', '#submit', saveSettings)
                    $('#settings_popup').on('click', '#send_email', sendEmail)
                    $('input').keypress(function (e) {
                      if (e.which === 13) {
                          $('#submit').trigger('click')
                      }
                    })
                }
            }
            $.get(
                this.href,
                {},
                function(resp, status, xhr) {
                    popup.html(resp)
                    popup.modal()
                }, 'html'
            )
        }
    }

    function newTime(evt) {
        var due = $(evt.target).find('input').val()
        var id  = $(evt.target).closest('tr').attr('id')
        $.post(
            '/mails/update/' + id + '/',
            {
                'due': due
            }
        ).done( function() {
            var duefield = $('#due-' + id)
            duefield.text(due)
        })
    }

    function saveSettings() {
        var address = $('#address').val()
        var anti_spam = $('#id_anti_spam').prop('checked')
        $.post(
            '/settings/',
            {
                address : address,
                anti_spam : anti_spam
            },
            function(data) {
                $('#settings_popup').html(data)
            }
        )
        .done (
            $('#address').val('')
        )
    }

    function deleteAddress(evt) {
        var row = $(evt.target).closest('tr')
        var id = $(evt.target).attr('id')
        return row.hide('slow')
        .done(
            $.post(
                '/settings/',
                {
                    user_id : id
                }
            )
        )
    }

    function sendEmail(evt) {
        var user_email = $(evt.target).next('input').val()
        return $.post(
            '/settings/',
            {
                user_email : user_email
            }
        )
    }

    function initiateDatetimepicker() {
        $('.date').datetimepicker({
            format: "YYYY-MM-DD hh:mm",
            minDate: new Date(),
            showToday: true,
            useCurrent: true,
            useSeconds: false,
            useMinutes: true,
            minuteStepping: 1,
            icons : {
                time: "fa fa-clock-o",
                date: "fa fa-calendar",
                up:   "fa fa-arrow-up",
                down: "fa fa-arrow-down"
            }
        })
        $('.date').on('dp.change', newTime)
    }

    function initiateSearch() {
        $('#searchMails').keyup(function() {
            var key = $(this).val()
            var regex = new RegExp(key, 'i')
            $('.item').each( function() {
                var subject = $(this).find('.subject').text()
                var sent = $(this).find('.sent').text()
                var due = $(this).find('.date').find('input').val()
                var texts = [subject, sent, due]
                if (regex.test(texts.join(' '))) {
                    $(this).show()
                }
                else {
                    $(this).hide()
                }
            })
        })
    }

    $('#list').on('click', '#delete-mail', ajaxPopup('delete'))
    $('#list').on('click', '#show-info', ajaxPopup('info'))
    $('#settings').click(ajaxPopup('settings'))
    $('#list').on('mouseover', '.add-popover', function(e) {$(e.target).popover()})

    function refresh() {
        // Do not poll when datepicker or search is active
        if ($('.bootstrap-datetimepicker-widget').is(':visible') ||
            $('#searchMails').val()){
            return
        }
        $.ajax({
            url: '/mails/table/',
            success: function(data) {
                $('#list').html(data)
                initiateDatetimepicker()
                initiateSearch()
            }
        })
    }

    function scheduleRefresh(){
        refresh()
        setTimeout(scheduleRefresh, 10 * 1000)
    }

    scheduleRefresh()

})();
