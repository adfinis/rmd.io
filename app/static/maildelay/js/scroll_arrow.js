$(".arrow-wrap").click(function() {
  $("html, body").animate(
    {
      scrollTop: $(".how-it-works").offset().top - 45
    },
    900
  );
});
