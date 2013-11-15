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
$('.form-datetime').datetimepicker({
    format: "yyyy-mm-dd hh:ii",
    todayBtn:  1,
    startDate: new Date(),
    autoclose: 1,
    todayHighlight: 1,
    pickerPosition: "bottom-right",
    minuteStep: 30,
});
$('.delete-button').click(function(evt){
    evt.preventDefault();
    var popup = $('#popup');
    if(popup.length == 0) {
        $('body').append('<div id="popup" class="modal fade" role="dialog"/>');
        popup = $('#popup');
    }
    $.get(
        this.href,
        {},
        function(resp, status, xhr) {
            popup.html(resp);
            popup.modal();
        }
    );
});
$(function() {
    $('.due').change(function() {
        var sent = $(this).closest('tr').find('.sent_date').text()
        var element = $(this).closest('td').find('.timedelta')
        $.post(
            $(this).closest('form').attr('action'),
            {due: this.value,}
        )
        .done( function() {
            updateDelta()
            $(element).effect("highlight", {color: '#58FA58'}, 2000)
        })
        .fail( function() {
            alert('Failed to change due date. Please try again.')
        });
    });
    function updateDelta() {
        $('.duedate').each(function(i, elem) {
            var due = $(elem).find('.due').val()
            var delta = $(elem).find('.timedelta')
            delta.text(moment(due, "YYYY-MM-DD HH:mm").fromNow())
            delta.attr("data-original-title", due)
            delta.tooltip({placement: 'left'})
        })
    }
    function scheduleUpdateDelta() {
        updateDelta();
        setTimeout(scheduleUpdateDelta, 20000);
    }
    function scheduleUpdate() {
        
    }
    scheduleUpdateDelta()
});
