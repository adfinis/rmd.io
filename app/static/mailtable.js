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
            }
            $.get(
                this.href,
                {},
                function(resp, status, xhr) {
                    popup.html(resp)
                    popup.modal()
                    if (name === 'settings') {
                        $('#settings_popup').on('click', '.delete-address', deleteAddress)
                        $('#settings_popup').on('click', '#submit', saveSettings)
                    }
                }, 'html'
            )
        }
    }

    function newTime(evt) {
        var duetext = $(evt.target).closest('td').find('.due-text')
        $.post(
            $(evt.target).closest('form').attr('action'),
            {due: evt.target.value}
        )
        .done( function() {
            updateDue()
            duetext.effect("highlight", {color: '#58FA58'}, 2000)
        })
        function updateDue() {
            $('.duedate').each(function(i, form) {
                var due = $(form).find('.date-form').val()
                var duetext = $(form).find('.due-text')
                duetext.text(due)
            })
        }
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
        row.hide('slow')
        .done(
            $.post(
                '/settings/',
                {
                    address_id : id
                }
            )
        )
    }

    $('#datatable_mails').on('click', '.delete-button', ajaxPopup('delete'))
    $('#settings').click(ajaxPopup('settings'))
    $('#terms').click(ajaxPopup('terms'))
    $('#help').click(ajaxPopup('help'))

    function refresh() {
        // Do not poll when datepicker is visible. This breaks it horribly
        if ($('.datetimepicker').is(':visible')) {
            return
        }
        // Do not poll when search is active. This breaks it
        if ($('#searchMails').val()) {
            return
        }

        $.ajax({
            url: '/table/',
            success: function(data) {
                $('#datatable_mails').html(data)
                $('.form-datetime').datetimepicker({
                    format: "yyyy-mm-dd hh:ii",
                    todayBtn:  1,
                    startDate: new Date(),
                    autoclose: 1,
                    todayHighlight: 1,
                    pickerPosition: "bottom-left",
                    minuteStep: 15,
                })
                $('.date-form').change(newTime)

                $('#searchMails').keyup(function() {
                    var key = $(this).val()
                    var regex = new RegExp(key, 'i')
                    $('.mailTableRow').each( function() {
                        var subject = $(this).find('.subject').text()
                        var recipient = $(this).find('.recipient').text()
                        if (regex.test(subject + ' ' + recipient)) {
                            $(this).show()
                        }
                        else {
                            $(this).hide()
                        }
                    })
                })
            }
        })
    }

    function scheduleRefresh(){
        refresh()
        setTimeout(scheduleRefresh, 10 * 1000)
    }

    scheduleRefresh()

})();
