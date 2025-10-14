define([
  "jQuery",
  "lodash",
  "js/entry/application_preview",
  "select2",
], function ($, _, applicationPreview) {
  function initAssessorsCommentsPopover(assessments) {
    var $contentContainer = $("<div>"),
      $viewAssessorsComments = $("#viewAssessorsComments");

    if (assessments.length) {
      $.each(assessments, function (index, assessment) {
        if (assessment.status === "Assessed") {
          var assessorGroupName =
            "<strong>" + assessment.assessor_group.name + ": </strong>";
          $contentContainer.append(
            $("<p>").html(assessorGroupName + assessment.comment)
          );
        }
      });
    }

    if ($contentContainer.children().length) {
      $contentContainer.find(":last-child").addClass("no-margin");
    } else {
      $contentContainer.append(
        $("<p>").addClass("no-margin").text("No assessors' comments available")
      );
    }

    if (typeof bootstrap !== "undefined" && bootstrap.Popover) {
      new bootstrap.Popover($viewAssessorsComments[0], {
        container: "body",
        content: $contentContainer,
        html: true,
      });
    } else {
      console.warn(
        "Bootstrap Popover not available; assessors comments popover not initialised."
      );
    }
  }

  function initDeclineStatus(reason) {
    var $declinedReasonContainer = $("<div>"),
      $status = $("#status");

    if ($status) {
      if (!reason) {
        $declinedReasonContainer.append($("<p>").html("No reason"));
      } else {
        reason.split("\n").forEach(function (reason) {
          $declinedReasonContainer.append($("<p>").html(reason));
        });
      }
      $status.html("").append("<a>Declined</a>");
      if (typeof bootstrap !== "undefined" && bootstrap.Popover) {
        new bootstrap.Popover($status[0], {
          container: "body",
          content: $declinedReasonContainer,
          html: true,
        });
      } else {
        console.warn(
          "Bootstrap Popover not available; declined reason popover not initialised."
        );
      }
    }
  }

  return {
    init: function (application, assessments) {
      applicationPreview.layoutPreviewItems(
        "#applicationContainer",
        application.licence_type.application_schema,
        application.data
      );
      initAssessorsCommentsPopover(assessments);
      if (application["processing_status"].toLowerCase() === "declined") {
        initDeclineStatus(application["declined_reason"] || "");
      }
    },
  };
});
