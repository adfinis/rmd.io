$(".arrow-wrap").click(function() {
    console.log($(".how-it-works"))
    $('html, body').animate({
        scrollTop: $(".how-it-works").offset().top - 45
    }, 2000);
});
