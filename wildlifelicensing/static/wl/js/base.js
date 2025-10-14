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

// Ensure Select2 uses the bootstrap-5 theme by default for calls that don't
// explicitly pass a theme. This keeps templates that call `.select2()` without
// options working after moving to the CDN/theme CSS.
require(["select2"], function () {
  if ($.fn && $.fn.select2 && $.fn.select2.defaults) {
    try {
      // select2 v4 exposes a defaults object; set theme if not already set
      if (!$.fn.select2.defaults.get("theme")) {
        $.fn.select2.defaults.set("theme", "bootstrap-5");
      }
    } catch (e) {
      // some select2 builds might not support defaults API; ignore silently
      // so we don't break pages if select2 is missing or older.
    }
  }
});
