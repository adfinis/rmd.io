(function (){
    "use strict";

    function ajaxPopup(evt) {
        evt.preventDefault()
        var name = $(this).data('name')
        var popup = $('#'+name+'_popup')
        if(popup.length === 0) {
            $('body').append('<div id="'+name+'_popup" class="modal fade" role="dialog"/>')
            popup = $('#'+name+'_popup')
            popup.modal()
        }
        $.get(
            $(this).prop('href'),
            {},
            function(resp, status, xhr) {
                popup.html(resp)
                popup.modal('show')
            }, 'html'
        )
    }

    $('body').on('click', '[data-target="dialog"]', ajaxPopup)

})();
