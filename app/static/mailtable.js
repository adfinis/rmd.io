$.ajaxSetup({ 
     beforeSend: function(xhr, settings) {
         function getCookie(name) {
             var cookieValue = null;
             if (document.cookie && document.cookie != '') {
                 var cookies = document.cookie.split(';');
                 for (var i = 0; i < cookies.length; i++) {
                     var cookie = jQuery.trim(cookies[i]);
                 if (cookie.substring(0, name.length + 1) == (name + '=')) {
                     cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                     break;
                 }
             }
         }
         return cookieValue;
         }
         if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
             xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
         }
     } 
});

function refresh() {
    // Do not poll when datepicker is visible. This breaks it horribly
    if ($('.datetimepicker').is(':visible')) {
        return;
    }
    $.ajax({
        url: '/table/',
        success: function(data) {
            $('#datatable_mails').html(data);

            $('.form-datetime').datetimepicker({
                format: "yyyy-mm-dd hh:ii",
                todayBtn:  1,
                startDate: new Date(),
                autoclose: 1,
                todayHighlight: 1,
                pickerPosition: "bottom-left",
                minuteStep: 15,
            });

            $('.delete-button').click(function(evt){
                evt.preventDefault();
                var delete_popup = $('#delete_popup');
                if(delete_popup.length == 0) {
                    $('body').append('<div id="delete_popup" class="modal fade" role="dialog"/>');
                    delete_popup = $('#delete_popup');
                }
                $.get(
                    this.href,
                    {},
                    function(resp, status, xhr) {
                        delete_popup.html(resp);
                        delete_popup.modal();
                    }
                );
            });

            $('#terms').click(function(evt){
                evt.preventDefault();
                var terms_popup = $('#terms_popup');
                if(terms_popup.length == 0) {
                    $('body').append('<div id="terms_popup" class="modal fade" role="dialog"/>');
                    terms_popup = $('#terms_popup');
                }
                $.get(
                    this.href,
                    {},
                    function(resp, status, xhr) {
                        terms_popup.html(resp);
                        terms_popup.modal();
                    }
                );
            });

            $('#help').click(function(evt){
                evt.preventDefault();
                var help_popup = $('#help_popup');
                if(help_popup.length == 0) {
                    $('body').append('<div id="help_popup" class="modal fade" role="dialog"/>');
                    help_popup = $('#help_popup');
                }
                $.get(
                    this.href,
                    {},
                    function(resp, status, xhr) {
                        help_popup.html(resp);
                        help_popup.modal();
                    }
                );
            });

            $(function() {
                $('.date-form').change(function() {
                    var delta = $(this).closest('td').find('.timedelta')
                    $.post(
                        $(this).closest('form').attr('action'),
                        {due: this.value}
                    )
                    .done( function() {
                        updateDelta()
                        $(delta).effect("highlight", {color: '#58FA58'}, 2000)
                    })
                    .fail( function() {
                        var error_popup = $('#error_popup');
                        if(error_popup.length == 0) {
                            $('body').append('<div id="error_popup" class="modal fade" role="dialog"/>');
                                error_popup = $('#error_popup');
                        }
                        $.get(
                            "/error/",
                            {},
                            function(resp, status, xhr) {
                                error_popup.html(resp);
                                error_popup.modal();
                            }
                        );
                    });
                });

                function updateDelta() {
                    $('.duedate').each(function(i, form) {
                        var due = $(form).find('.date-form').val()
                        var delta = $(form).find('.timedelta')
                        delta.text(moment(due, "YYYY-MM-DD HH:mm").fromNow())
                        delta.attr("data-original-title", due)
                        delta.tooltip({placement: 'left'})
                    })
                }
                function scheduleUpdateDelta() {
                    updateDelta();
                    setTimeout(scheduleUpdateDelta, 10000);
                }
                scheduleUpdateDelta()
            });

            $(function() {
                $('#searchMails').keyup(function() {
                    var key = $(this).val()
                    var regex = new RegExp(key, 'i')
                    $('.mailTableRow').each( function() {
                        var subject = $(this).find('.subject').text()
                        if (subject.search(regex) < 0) {
                            $(this).hide()
                        }
                        else {
                            $(this).show()
                        }
                    })
                })
            });
        }
    })
};

function scheduleRefresh(){
    refresh();
    setTimeout(scheduleRefresh, 10000)
};

scheduleRefresh();
