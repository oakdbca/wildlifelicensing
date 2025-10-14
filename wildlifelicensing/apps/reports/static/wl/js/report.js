define(["jQuery", "bootstrap-datetimepicker", "select2"], function ($) {
  "use strict";

  function initDatePicker() {
    $("[name$='date']").datetimepicker({
      format: "DD/MM/YYYY",
    });
  }

  function initRegionSelector() {
    var $select = $("#licence-form").find("select");
    $select.select2({
      theme: 'bootstrap-5',
      placeholder: "Select region(s) or blank for all.",
    });
    $select.removeClass("hidden");
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
