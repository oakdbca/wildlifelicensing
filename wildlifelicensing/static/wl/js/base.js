require(["jQuery", "bootstrap"], function ($, bootstrap) {
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

  // Migration helper: convert legacy Bootstrap 3 collapse markup (panel-collapse.in)
  // to Bootstrap 5 expected classes (.collapse.show) and ensure toggler elements
  // have correct `collapsed` class and `aria-expanded` attribute. This prevents
  // state mismatches where a toggle appears to close but the element re-opens
  // because the JS interprets the initial state differently.
  $(function () {
    // Convert element-level classes
    $(".panel-collapse.in").each(function () {
      var $el = $(this);
      // Add the BS5 classes and remove the legacy 'in'
      $el.addClass("collapse show").removeClass("in");
    });

    // Sync toggler controls (href or data-bs-target)
    $('[data-bs-toggle="collapse"]').each(function () {
      var $t = $(this);
      var target =
        $t.attr("href") || $t.attr("data-bs-target") || $t.attr("data-target");
      if (!target) return;
      try {
        var $targetEl = $(target);
        if ($targetEl.length) {
          var isShown = $targetEl.hasClass("show");
          // toggler should have 'collapsed' when target is not shown
          $t.toggleClass("collapsed", !isShown);
          $t.attr("aria-expanded", isShown ? "true" : "false");
        }
      } catch (err) {
        // invalid selector in href (e.g., javascript:void(0)) — ignore
      }
    });

    // Prevent anchors used as UI controls from jumping to the top of the page.
    // Many templates use <a href="#" role="button"> or anchors with
    // data-bs-toggle/data-toggle to act as buttons. Intercept clicks on
    // exact '#' (and javascript:void(0)) targets and prevent default when
    // the anchor is clearly being used as a control. This preserves real
    // fragment navigation (e.g., href="#some-id") while stopping the
    // undesired scroll-to-top behaviour.
    $(document).on(
      "click",
      'a[href="#"], a[href="javascript:void(0)"]',
      function (e) {
        var $a = $(this);
        var isControl =
          $a.attr("role") === "button" ||
          typeof $a.attr("data-bs-toggle") !== "undefined" ||
          typeof $a.attr("data-toggle") !== "undefined" ||
          typeof $a.attr("data-bs-target") !== "undefined" ||
          typeof $a.attr("data-target") !== "undefined";
        if (isControl) {
          e.preventDefault();
        }
      }
    );
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
