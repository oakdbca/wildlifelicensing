require(["jQuery", "bootstrap"], function ($) {
  // bootstrap returns nothing so must go last in required modules
  $("body").on("click", function (e) {
    $('[data-bs-toggle="popover"]').each(function () {
      //the 'is' for buttons that trigger popups
      //the 'has' for icons within a button that triggers a popup
      if (
        !$(this).is(e.target) &&
        $(this).has(e.target).length === 0 &&
        $(e.target).parents(".popover").length === 0 &&
        $.contains(document, e.target)
      ) {
        var inst = bootstrap.Popover.getInstance(this);
        if (inst) {
          inst.hide();
        }
      }
    });
  });

  // Previously we applied a Bootstrap 3 workaround here (manipulating internal popover state)
  // which is not applicable to Bootstrap 5 and can throw when the internal data structure
  // isn't present. Keep an empty handler for the event to avoid errors on pages that
  // still trigger 'hidden.bs.popover'. If future debugging shows a need, we can add
  // a migration-specific behavior here.
  $("body").on("hidden.bs.popover", function (e) {
    // no-op for Bootstrap 5 compatibility
  });
});
