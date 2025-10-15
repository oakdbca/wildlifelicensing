define(["jQuery", "bootstrap-datetimepicker", "select2"], function ($) {
  "use strict";

  function initDatePicker() {
    $("[name$='date']").datetimepicker({
      format: "DD/MM/YYYY",
    });
  }

  function initRegionSelector() {
    var $selects = $("#licence-form").find("select");
    // Initialize each select after removing the 'hidden' class so Select2 can
    // correctly calculate widths. Also force width: '100%' and set a
    // reasonable dropdownParent to avoid positioning issues inside layout.
    $selects.each(function () {
      var $s = $(this);
      $s.removeClass("d-none");
      // If a prior Select2 instance exists (e.g., due to hot-reload), destroy it
      if ($s.hasClass("select2-hidden-accessible")) {
        $s.select2("destroy");
      }
      $s.select2({
        theme: "bootstrap-5",
        placeholder: "Select region(s) or blank for all.",
        width: "100%",
        // Append dropdown to body to avoid clipping/overflow issues inside
        // nested containers (keeps the dropdown aligned to the control).
        dropdownParent: $(document.body),
      });
    });
  }

  function initPaymentsDatePicker() {
    var $form = $("#payments-form");
    $form.find("input:text").datetimepicker({
      format: "DD/MM/YYYY HH:mm:SS",
    });
  }

  return {
    initialise: function () {
      initDatePicker();
      initRegionSelector();
      initPaymentsDatePicker();
    },
  };
});
