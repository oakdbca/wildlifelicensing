define([
  "jQuery",
  "bootstrap-datetimepicker",
  "select2",
  "bootstrap-3-typeahead",
], function ($) {
  "use strict";

  // small helper for initializing tooltips with Bootstrap 5 API (fallback to jQuery tooltip)
  function bsTooltipInit($el, opts) {
    var el = $el && $el.length ? $el.get(0) : $el;
    if (!el) return;
    opts = opts || {};
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
      if (!bootstrap.Tooltip.getInstance(el)) {
        new bootstrap.Tooltip(el, opts);
      }
    } else if ($el && $el.tooltip) {
      $el.tooltip(opts);
    } else {
      console.warn(
        "Tooltip not initialised: bootstrap and jQuery.tooltip unavailable"
      );
    }
  }

  return {
    initialise: function () {
      var $issueLicenceForm = $("#issueLicenceForm"),
        $issueButton = $("#issue"),
        $regionSelect = $issueLicenceForm.find("#id_regions"),
        $addAttachment = $("#add_attachment");

      // initialise all datapickers
      $("input[id$='date']").each(function () {
        $(this).datetimepicker({
          format: "DD/MM/YYYY",
        });
      });

      function _submitForm(e) {
        if (!$(this).hasClass("disabled")) {
          $issueLicenceForm.append(
            $("<input>")
              .attr("type", "hidden")
              .attr("name", "submissionType")
              .val(this.id)
          );
          $issueLicenceForm.submit();
        }
      }

      $("#save").click(_submitForm);

      $issueButton.click(_submitForm);

      if ($issueButton.hasClass("disabled")) {
        // initialize Bootstrap 5 tooltip if available, otherwise fall back to jQuery tooltip
        bsTooltipInit($issueButton, {});
      }

      $("#previewLicence").click(function (e) {
        $issueLicenceForm.find(".extracted-checkbox").each(function () {
          $issueLicenceForm
            .find("#" + this.id + "Hidden")
            .prop("disabled", this.checked);
        });
        var url = this.href + "?" + $issueLicenceForm.serialize();
        window.open(url);
        $issueLicenceForm.find("input:hidden").prop("disabled", false);
        return false;
      });

      $regionSelect.select2({
        theme: "bootstrap-5",
        placeholder: "Select applicable regions.",
      });
      $regionSelect.removeClass("d-none");

      $(".species").each(function () {
        var speciesTypeArg = "";
        if ($(this).attr("data-species-type") !== undefined) {
          speciesTypeArg = "&type=" + $(this).attr("data-species-type");
        }

        // initialise species typeahead
        $(this).typeahead({
          minLength: 3,
          items: "all",
          source: function (query, process) {
            return $.get(
              "/taxonomy/species_name?search=" + query + speciesTypeArg,
              function (data) {
                return process(data);
              }
            );
          },
        });
      });

      $addAttachment.on("click", function (e) {
        var inputNode = $(
          '<input class="top-buffer" id="id_attach" name="attachments" type="file" multiple>'
        );
        e.preventDefault();
        $(e.target).parent().append(inputNode);
        inputNode.click();
      });
    },
  };
});
