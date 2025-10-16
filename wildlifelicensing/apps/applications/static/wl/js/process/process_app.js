define([
  "jQuery",
  "js/process/preview_versions",
  "js/wl.dataTable",
  "moment",
  "lodash",
  "bootstrap",
  "select2",
], function ($, previewVersions, dataTable, moment, _) {
  "use strict";

  // Helper: initialize/dispose tooltip using Bootstrap 5 API when available,
  // otherwise fall back to jQuery tooltip() if present. Logs a warning if
  // neither is available.
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
        "Tooltip not initialised: bootstrap and jQuery.tooltip both unavailable"
      );
    }
  }

  function bsTooltipDestroy($el) {
    var el = $el && $el.length ? $el.get(0) : $el;
    if (!el) return;
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
      var inst = bootstrap.Tooltip.getInstance(el);
      if (inst) inst.dispose();
    } else if ($el && $el.tooltip) {
      // Some environments include a jQuery tooltip plugin that uses "destroy",
      // while Bootstrap 5's jQuery bridge expects "dispose". Try dispose first,
      // then fall back to destroy for older plugins. Wrap in try/catch to avoid
      // throwing if the method isn't supported.
      try {
        $el.tooltip("dispose");
      } catch (e) {
        try {
          $el.tooltip("destroy");
        } catch (e2) {
          // ignore
        }
      }
    }
  }

  // Helper: initialize/dispose popover using Bootstrap 5 API when available,
  // otherwise fall back to jQuery popover() if present. If neither is
  // available yet (script still loading) retry for a short time before
  // warning — this helps when scripts load asynchronously (CDNs, requirejs).
  function bsPopoverInit($el, opts, warnMessage) {
    var el = $el && $el.length ? $el.get(0) : $el;
    if (!el) return;
    opts = opts || {};
    warnMessage =
      warnMessage ||
      "Bootstrap Popover not available; popover not initialised.";

    var tries = 0;
    var maxTries = 20; // ~2 seconds at 100ms intervals

    function tryInit() {
      if (typeof bootstrap !== "undefined" && bootstrap.Popover) {
        try {
          if (!bootstrap.Popover.getInstance(el)) {
            new bootstrap.Popover(el, opts);
          }
          return;
        } catch (e) {
          // fall through to retry/fallback
        }
      }
      // jQuery UI or older plugins may expose popover on the jQuery object
      try {
        if ($el && $el.popover) {
          $el.popover(opts);
          return;
        }
      } catch (e) {
        // ignore and retry
      }

      if (tries++ < maxTries) {
        setTimeout(tryInit, 100);
      } else {
        console.warn(warnMessage);
      }
    }

    tryInit();
  }

  function bsPopoverDestroy($el) {
    var el = $el && $el.length ? $el.get(0) : $el;
    if (!el) return;
    if (typeof bootstrap !== "undefined" && bootstrap.Popover) {
      var inst = bootstrap.Popover.getInstance(el);
      if (inst) inst.dispose();
    } else if ($el && $el.popover) {
      try {
        $el.popover("dispose");
      } catch (e) {
        try {
          $el.popover("destroy");
        } catch (e2) {
          /* ignore */
        }
      }
    }
  }

  var application,
    assessments,
    amendmentRequests,
    csrfToken,
    $processingStatus,
    $previewContainer,
    moduleData;

  function initAssignee(officersList, user) {
    var $assignee = $("#assignee");

    $assignee.select2({
      data: officersList,
      initSelection: function (element, callback) {
        if (application.assigned_officer) {
          callback({
            id: application.assigned_officer.id,
            text:
              application.assigned_officer.first_name +
              " " +
              application.assigned_officer.last_name,
          });
        } else {
          callback({ id: 0, text: "Unassigned" });
        }
      },
    });

    $assignee.on("change", function (e) {
      $.post(
        "/applications/assign-officer/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          userID: e.val,
        },
        function (data) {
          $processingStatus.text(data.processing_status);
        }
      );
    });

    $("#assignToMe").click(function () {
      $.post(
        "/applications/assign-officer/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          userID: user.id,
        },
        function (data) {
          $assignee.select2("data", data.assigned_officer);
          $processingStatus.text(data.processing_status);
        }
      );
    });
  }

  function initLodgedVersions(previousData) {
    var $table = $("#lodgedVersions");
    $.each(previousData, function (index, version) {
      var $row = $("<tr>"),
        $compareLink,
        $comparingText,
        $actionSpan;

      $row.append($("<td>").text(version.lodgement_number));
      $row.append($("<td>").text(version.date));

      if (index === 0) {
        $compareLink = $("<a>")
          .text("Show")
          .addClass("d-none")
          .attr("href", "#")
          .attr("role", "button")
          .click(function (e) {
            e.preventDefault();
          });
        $comparingText = $("<p>")
          .css("font-style", "italic")
          .text("Showing")
          .addClass("no-margin");

        $row.addClass("small-table-selected-row");
      } else {
        $compareLink = $("<a>")
          .text("Compare")
          .attr("href", "#")
          .attr("role", "button")
          .click(function (e) {
            e.preventDefault();
          });
        $comparingText = $("<p>")
          .css("font-style", "italic")
          .text("Comparing")
          .addClass("no-margin")
          .addClass("d-none");
      }

      $actionSpan = $("<span>").append($compareLink).append($comparingText);

      $compareLink.click(function (e) {
        $(document).trigger("application-version-selected");
        $row.addClass("small-table-selected-row");
        $compareLink.addClass("d-none");
        $comparingText.removeClass("d-none");
        $previewContainer.empty();
        previewVersions.layoutPreviewItems(
          $previewContainer,
          moduleData.form_structure,
          application.data,
          version.data
        );
      });

      $row.append($("<td>").html($actionSpan));

      $table.append($row);
    });

    $(document).on("application-version-selected", function () {
      $table.find("tr").removeClass("small-table-selected-row");
      $table.find("a").removeClass("d-none");
      $table.find("p").addClass("d-none");
    });
  }

  function initPreviousApplication() {
    if (!application.previous_application) {
      return;
    }

    var $table = $("#previousApplication");

    var $row = $("<tr>"),
      $compareLink;
    $row.append(
      $("<td>").text(application.previous_application.lodgement_number)
    );
    $row.append(
      $("<td>").text(application.previous_application.lodgement_date)
    );

    var $compareLink = $("<a>Compare</a>")
      .attr("href", "#")
      .attr("role", "button")
      .click(function (e) {
        e.preventDefault();
      });

    var $comparingText = $("<p>")
      .css("font-style", "italic")
      .text("Comparing")
      .addClass("no-margin")
      .addClass("d-none");

    var $actionSpan = $("<span>").append($compareLink).append($comparingText);

    $compareLink.click(function (e) {
      $(document).trigger("application-version-selected");
      $row.addClass("small-table-selected-row");
      $compareLink.addClass("d-none");
      $comparingText.removeClass("d-none");
      $previewContainer.empty();
      previewVersions.layoutPreviewItems(
        $previewContainer,
        moduleData.form_structure,
        application.data,
        application.previous_application.data
      );
    });

    $row.append($("<td>").html($actionSpan));

    $table.append($row);

    $(document).on("application-version-selected", function () {
      $table.find("tr").removeClass("small-table-selected-row");
      $compareLink.removeClass("d-none");
      $comparingText.addClass("d-none");
    });
  }

  function initIDCheck() {
    var $container = $("#idCheck");

    if (!application.licence_type.identification_required) {
      $container.addClass("d-none");
      return;
    }

    var $actionButtonsContainer = $container.find(".action-buttons-group"),
      $done = $container.find(".done"),
      $resetLink = $done.find("a"),
      $status = $container.find(".status");

    if (application.id_check_status === "Accepted") {
      $actionButtonsContainer.addClass("d-none");
      $status.addClass("d-none");
      $done.removeClass("d-none");
    }

    $resetLink.click(function () {
      $.post(
        "/applications/set-id-check-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "not_checked",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $actionButtonsContainer.removeClass("d-none");
          $status.text(data.id_check_status);
          $status.removeClass("d-none");
          $done.addClass("d-none");

          application.id_check_status = data.id_check_status;
          determineApplicationApprovable();
        }
      );
    });

    var $acceptButton = $actionButtonsContainer.find(".btn-success"),
      $requestUpdateButton = $actionButtonsContainer.find(".btn-warning");

    $acceptButton.click(function () {
      $.post(
        "/applications/set-id-check-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "accepted",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $status.addClass("d-none");
          $done.removeClass("d-none");
          $actionButtonsContainer.addClass("d-none");

          application.id_check_status = data.id_check_status;
          determineApplicationApprovable();
        }
      );
    });

    var $requestIDUpdateModal = $("#requestIDUpdateModal"),
      $idRequestForm = $requestIDUpdateModal.find("#idRequestForm"),
      $idReason = $idRequestForm.find("#id_reason"),
      $idText = $idRequestForm.find("#id_text");

    $requestUpdateButton.click(function () {
      if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
        var modal = bootstrap.Modal.getOrCreateInstance(
          $requestIDUpdateModal[0]
        );
        modal.show();
      } else if ($requestIDUpdateModal.modal) {
        $requestIDUpdateModal.modal("show");
      }
    });

    $idRequestForm.submit(function (e) {
      $.ajax({
        type: $(this).attr("method"),
        url: $(this).attr("action"),
        data: $(this).serialize(),
        success: function (data) {
          $processingStatus.text(data.processing_status);
          $container.find(".status").text(data.id_check_status);
          $idReason.find("option:eq(0)").prop("selected", true);
          $idText.val("");

          application.id_check_status = data.id_check_status;
          determineApplicationApprovable();

          if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
            var modal = bootstrap.Modal.getInstance($requestIDUpdateModal[0]);
            if (modal) {
              modal.hide();
            }
          } else if ($requestIDUpdateModal.modal) {
            $requestIDUpdateModal.modal("hide");
          }
        },
      });

      e.preventDefault();
    });
  }

  function initReturnsCheck() {
    var $container = $("#returnsCheck");

    // for new applications or applications that are licence amendments, no need to check returns
    if (application.application_type !== "renewal") {
      $container.addClass("d-none");
      return;
    }

    var $actionButtonsContainer = $container.find(".action-buttons-group"),
      $done = $container.find(".done"),
      $resetLink = $done.find("a"),
      $status = $container.find(".status");

    if (application.returns_check_status === "Accepted") {
      $actionButtonsContainer.addClass("d-none");
      $status.addClass("d-none");
      $done.removeClass("d-none");
    }

    $resetLink.click(function () {
      $.post(
        "/applications/set-returns-check-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "not_checked",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $actionButtonsContainer.removeClass("d-none");
          $status.text(data.returns_check_status);
          $status.removeClass("d-none");
          $done.addClass("d-none");

          application.returns_check_status = data.returns_check_status;
          determineApplicationApprovable();
        }
      );
    });

    var $acceptButton = $actionButtonsContainer.find(".btn-success"),
      $requestReturnsButton = $actionButtonsContainer.find(".btn-warning");

    $acceptButton.click(function () {
      $.post(
        "/applications/set-returns-check-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "accepted",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $status.addClass("d-none");
          $done.removeClass("d-none");
          $actionButtonsContainer.addClass("d-none");

          application.returns_check_status = data.returns_check_status;
          determineApplicationApprovable();
        }
      );
    });

    var $requestReturnsModal = $("#requestReturnsModal"),
      $returnsRequestForm = $requestReturnsModal.find("#returnsRequestForm"),
      $returnsReason = $returnsRequestForm.find("#id_reason"),
      $returnsText = $returnsRequestForm.find("#id_text");

    $requestReturnsButton.click(function () {
      if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
        bootstrap.Modal.getOrCreateInstance($requestReturnsModal.get(0)).show();
      } else if ($requestReturnsModal.modal) {
        $requestReturnsModal.modal("show");
      }
    });

    $returnsRequestForm.submit(function (e) {
      $.ajax({
        type: $(this).attr("method"),
        url: $(this).attr("action"),
        data: $(this).serialize(),
        success: function (data) {
          $processingStatus.text(data.processing_status);
          $container.find(".status").text(data.returns_check_status);
          $returnsReason.find("option:eq(0)").prop("selected", true);
          $returnsText.val("");

          application.returns_check_status = data.returns_check_status;
          determineApplicationApprovable();

          if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
            var __inst = bootstrap.Modal.getInstance(
              $requestReturnsModal.get(0)
            );
            if (__inst) {
              __inst.hide();
            }
          } else if ($requestReturnsModal.modal) {
            $requestReturnsModal.modal("hide");
          }
        },
      });

      e.preventDefault();
    });
  }

  function initCharacterCheck() {
    var $container = $("#characterCheck"),
      $actionButtonsContainer = $container.find(".action-buttons-group"),
      $done = $container.find(".done"),
      $resetLink = $done.find("a"),
      $status = $container.find(".status"),
      $showCharacterChecklist = $container.find("#showCharacterChecklist"),
      $dodgyUser = $container.find("#dodgyUser");

    if (application.character_check_status === "Accepted") {
      $actionButtonsContainer.addClass("d-none");
      $status.addClass("d-none");
      $showCharacterChecklist.addClass("d-none");
      $dodgyUser.addClass("d-none");
      $done.removeClass("d-none");
    }

    $resetLink.click(function () {
      $.post(
        "/applications/set-character-check-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "not_checked",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $actionButtonsContainer.removeClass("d-none");
          $status.text(data.character_check_status);
          $status.removeClass("d-none");
          $showCharacterChecklist.removeClass("d-none");
          if (application.applicant_profile.user.character_flagged) {
            $dodgyUser.removeClass("d-none");
          }

          $done.addClass("d-none");

          application.character_check_status = data.character_check_status;
          determineApplicationApprovable();
        }
      );
    });

    var $acceptButton = $actionButtonsContainer.find(".btn-success");

    $acceptButton.click(function () {
      $.post(
        "/applications/set-character-check-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "accepted",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $status.addClass("d-none");
          $done.removeClass("d-none");
          $actionButtonsContainer.addClass("d-none");
          $showCharacterChecklist.addClass("d-none");
          $dodgyUser.addClass("d-none");

          application.character_check_status = data.character_check_status;
          determineApplicationApprovable();
        }
      );
    });

    var $characterChecklist = $("<ul>").addClass("popover-checklist");

    $characterChecklist.append($("<li>").text("Character flag in database"));
    $characterChecklist.append($("<li>").text("Police record check"));

    bsPopoverInit(
      $showCharacterChecklist,
      {
        container: "body",
        content: $characterChecklist.prop("outerHTML"),
        html: true,
      },
      "Bootstrap Popover not available; character checklist popover not initialised."
    );
    // Prevent default anchor navigation which jumps to top of page when href="#"
    $showCharacterChecklist.click(function (e) {
      e.preventDefault();
    });

    if (application.applicant_profile.user.character_flagged) {
      bsTooltipInit($dodgyUser, { container: "body" });
    }
  }

  function prepareAmendmentRequestsPopover($showPopover) {
    var $content = $("<ul>").addClass("popover-checklist");
    $.each(amendmentRequests, function (index, value) {
      $content.append($("<li>").text(value.reason + ": " + value.text));
    });

    // check if popover instance exists; if not create one; otherwise update content
    // Try to initialise or update using the helper which will retry briefly
    // while scripts load and fall back to jQuery if available.
    bsPopoverInit(
      $showPopover,
      {
        container: "body",
        content: $content.prop("outerHTML"),
        html: true,
      },
      "Bootstrap Popover not available; amendment requests popover not initialised."
    );
    // ensure visible if content exists
    if (amendmentRequests.length > 0) {
      $showPopover.removeClass("d-none");
    }
  }

  function initReview() {
    var $container = $("#review");

    var $actionButtonsContainer = $container.find(".action-buttons-group"),
      $done = $container.find(".done"),
      $status = $container.find(".status"),
      $acceptButton = $actionButtonsContainer.find(".btn-success"),
      $resetLink = $done.find("a"),
      $requestAmendmentButton = $actionButtonsContainer.find(".btn-warning"),
      $showAmendmentRequests = $container.find("#showAmendmentRequests");

    if (amendmentRequests.length > 0) {
      prepareAmendmentRequestsPopover($showAmendmentRequests);
    }

    if (application.review_status === "Accepted") {
      $actionButtonsContainer.addClass("d-none");
      $status.addClass("d-none");
      $showAmendmentRequests.addClass("d-none");
      $done.removeClass("d-none");
    }

    $resetLink.click(function () {
      $.post(
        "/applications/set-review-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "not_reviewed",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $actionButtonsContainer.removeClass("d-none");
          $status.text(data.review_status);
          $status.removeClass("d-none");
          if (amendmentRequests.length > 0) {
            $showAmendmentRequests.removeClass("d-none");
          }
          $done.addClass("d-none");

          application.review_status = data.review_status;
          determineApplicationApprovable();
        }
      );
    });

    $acceptButton.click(function () {
      $.post(
        "/applications/set-review-status/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          status: "accepted",
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $status.addClass("d-none");
          $actionButtonsContainer.addClass("d-none");
          $showAmendmentRequests.addClass("d-none");
          $done.removeClass("d-none");
          application.review_status = data.review_status;
          determineApplicationApprovable();
        }
      );
    });

    var $requestAmendmentModal = $("#requestAmendmentModal"),
      $amendmentRequestForm = $requestAmendmentModal.find(
        "#amendmentRequestForm"
      ),
      $idReason = $amendmentRequestForm.find("#id_reason"),
      $idText = $amendmentRequestForm.find("#id_text");

    $requestAmendmentButton.click(function () {
      if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
        bootstrap.Modal.getOrCreateInstance(
          $requestAmendmentModal.get(0)
        ).show();
      } else if ($requestAmendmentModal.modal) {
        $requestAmendmentModal.modal("show");
      }
    });

    $amendmentRequestForm.submit(function (e) {
      $.ajax({
        type: $(this).attr("method"),
        url: $(this).attr("action"),
        data: $(this).serialize(),
        success: function (data) {
          $processingStatus.text(data.processing_status);
          $status.text(data.review_status);
          $idReason.find("option:eq(0)").prop("selected", true);
          $idText.val("");

          application.review_status = data.review_status;
          determineApplicationApprovable();

          if (data.review_status === "Awaiting Amendments") {
            // ensure amendmentRequests is an array (server may return null/object)
            if (!Array.isArray(amendmentRequests)) {
              amendmentRequests = amendmentRequests ? [amendmentRequests] : [];
            }
            amendmentRequests.push(data.amendment_request);
            prepareAmendmentRequestsPopover($showAmendmentRequests);
          }

          if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
            var __amInst = bootstrap.Modal.getInstance(
              $requestAmendmentModal.get(0)
            );
            if (__amInst) {
              __amInst.hide();
            }
          } else if ($requestAmendmentModal.modal) {
            $requestAmendmentModal.modal("hide");
          }
        },
      });

      e.preventDefault();
    });
  }

  function createAssessmentRow(assessment) {
    var $row = $("<tr>"),
      $statusColumn = $("<td>").addClass("center"),
      $remind = $("<p>")
        .addClass("center")
        .addClass("no-margin")
        .append(
          $("<a>")
            .text("Remind")
            .attr("href", "#")
            .attr("role", "button")
            .click(function (e) {
              e.preventDefault();
            })
        ),
      $reassess = $("<p>")
        .addClass("center")
        .addClass("no-margin")
        .append(
          $("<a>")
            .text("Reassess")
            .attr("href", "#")
            .attr("role", "button")
            .click(function (e) {
              e.preventDefault();
            })
        );

    $row.append("<td>" + assessment.assessor_group.name + "</td>");

    $remind.click(function () {
      $.post(
        "/applications/remind-assessment/",
        {
          assessmentID: assessment.id,
          csrfmiddlewaretoken: csrfToken,
        },
        function (data) {
          if (data === "ok") {
            window.alert("Reminder sent");
          }
        }
      );
    });

    $reassess.click(function () {
      $.post(
        "/applications/send-for-assessment/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          assGroupID: assessment.assessor_group.id,
        },
        function (data) {
          $processingStatus.text(data.processing_status);

          $statusColumn.empty();
          $statusColumn.append(data.assessment.status);
          $statusColumn.append($remind);

          determineApplicationApprovable();
        }
      );
    });

    $statusColumn.append(assessment.status);

    if (assessment.status === "Awaiting Assessment") {
      $statusColumn.append($remind);
    } else {
      if (assessment.comment) {
        var $viewComment = $("<p>")
          .addClass("center")
          .addClass("no-margin")
          .append(
            $("<a>")
              .text("View Comment")
              .attr("data-bs-toggle", "popover")
              .attr("href", "#")
              .attr("role", "button")
              .click(function (e) {
                e.preventDefault();
              })
          );
        bsPopoverInit(
          $viewComment,
          {
            container: "body",
            content: assessment.comment,
            html: true,
          },
          "Bootstrap Popover not available; assessment comment popover not initialised."
        );
        $statusColumn.append($viewComment);
      }
      $statusColumn.append($reassess);
    }

    $row.append($statusColumn);
    return $row;
  }

  function initAssessment(assessorsList) {
    var $assessor = $("#assessor"),
      $sendForAssessment = $("#sendForAssessment"),
      $currentAssessments = $("#currentAssessments");

    $assessor.select2({
      theme: "bootstrap-5",
      data: assessorsList,
    });

    if (assessments.length > 0) {
      $.each(assessments, function (index, assessment) {
        $currentAssessments.append(createAssessmentRow(assessment));
      });
      $currentAssessments.parent().removeClass("d-none");
    }

    $assessor.on("change", function () {
      $sendForAssessment.prop("disabled", false);
    });

    $sendForAssessment.click(function () {
      $.post(
        "/applications/send-for-assessment/",
        {
          applicationID: application.id,
          csrfmiddlewaretoken: csrfToken,
          assGroupID: $assessor.val(),
        },
        function (data) {
          $processingStatus.text(data.processing_status);
          $currentAssessments.append(createAssessmentRow(data.assessment));
          $assessor.select2("val", "");

          // remove assessor from assessors list
          for (var i = 0; i < assessorsList.length; i++) {
            if (assessorsList[i].id === data.assessment.assessor_group.id) {
              assessorsList.splice(i, 1);
              break;
            }
          }

          $currentAssessments.parent().removeClass("d-none");

          assessments.push(data.assessment);
          determineApplicationApprovable();
        }
      );

      $sendForAssessment.prop("disabled", true);
    });
  }

  function determineApplicationApprovable() {
    var $submissionForm = $("#submissionForm"),
      $approve = $submissionForm.find("#approve"),
      $decline = $submissionForm.find("#decline"),
      $buttonClicked,
      approvableConditions = [
        (application.licence_type.identification_required &&
          application.id_check_status === "Accepted") ||
          !application.licence_type.identification_required,
        (application.application_type === "renewal" &&
          application.returns_check_status === "Accepted") ||
          application.application_type != "renewal",
        application.character_check_status === "Accepted",
        application.review_status === "Accepted",
      ];

    // ensure form only submits when either approve (enterConditions) is enabled or decline is clicked
    $($approve).click(function () {
      $buttonClicked = $(this);
    });

    $($decline).click(function () {
      $buttonClicked = $(this);
      declineApplication();
    });

    $submissionForm.submit(function (e) {
      if ($buttonClicked.is($approve) && $approve.hasClass("disabled")) {
        e.preventDefault();
      }
    });

    if (_.every(approvableConditions)) {
      $approve.removeClass("disabled");
      bsTooltipDestroy($approve);
    } else {
      $approve.addClass("disabled");
      bsTooltipInit($approve, {});
    }
  }

  function declineApplication() {
    var $modal = $("#declinedDetailsModal");
    if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
      bootstrap.Modal.getOrCreateInstance($modal.get(0)).show();
    } else if ($modal.modal) {
      $modal.modal("show");
    }
  }

  return {
    initialiseApplicationProcesssing: function (data) {
      $processingStatus = $("#processingStatus");
      $previewContainer = $("#previewContainer");
      csrfToken = data.csrf_token;
      application = data.application;
      assessments = data.assessments;
      amendmentRequests = data.amendment_requests;
      moduleData = data;

      initAssignee(data.officers, data.user);
      initLodgedVersions(data.previous_versions);
      initPreviousApplication();
      initIDCheck();
      initReturnsCheck();
      initCharacterCheck();
      initReview();
      initAssessment(data.assessor_groups);
      determineApplicationApprovable();

      previewVersions.layoutPreviewItems(
        $previewContainer,
        data.form_structure,
        application.data,
        application.data
      );
    },
    initialiseSidePanelAffix: function () {
      var $sidebarPanels = $("#sidebarPanels");
      $sidebarPanels.affix({ offset: { top: $sidebarPanels.offset().top } });
    },
  };
});
