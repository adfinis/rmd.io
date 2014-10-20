(function (){
    "use strict";

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
                }, 'html'
            )
        }
    }

    $('#terms').click(ajaxPopup('terms'))
    $('#help').click(ajaxPopup('help'))

})();
