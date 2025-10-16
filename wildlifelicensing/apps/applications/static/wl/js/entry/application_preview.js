define([
  "jQuery",
  "handlebars.runtime",
  "bootstrap",
  "js/handlebars_helpers",
  "js/precompiled_handlebars_templates",
], function ($, Handlebars) {
  function _setupDisclaimers(disclaimersSelector, lodgeSelector) {
    var $disclaimers = $(disclaimersSelector),
      $lodge = $(lodgeSelector),
      $form = $lodge.parents("form"),
      $buttonClicked;

    // local small helpers for tooltip init/destroy with Bootstrap 5 API and jQuery fallback
    function _bsTooltipInit($el, opts) {
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

    function _bsTooltipDestroy($el) {
      var el = $el && $el.length ? $el.get(0) : $el;
      if (!el) return;
      if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
        var inst = bootstrap.Tooltip.getInstance(el);
        if (inst) inst.dispose();
      } else if ($el && $el.tooltip) {
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

    if ($lodge.hasClass("disabled")) {
      _bsTooltipInit($lodge, {});
    }

    // ensure form only submits when either approve (enterConditions) is enabled or decline is clicked
    $(lodgeSelector).click(function () {
      $buttonClicked = $(this);
    });

    $form.submit(function (e) {
      if ($buttonClicked.is($lodge) && $lodge.hasClass("disabled")) {
        e.preventDefault();
      }
    });

    // enable lodge button if the number of checked checkboxes is the same as the number of
    // checkboxes in the dislaimer div (which is the parent of the disclaimers selector's elements)
    $(disclaimersSelector).change(function (e) {
      if (
        $(disclaimersSelector).parent().find(":checked").length ===
        $(disclaimersSelector).length
      ) {
        $lodge.removeClass("disabled");
        _bsTooltipDestroy($lodge);
      } else {
        $lodge.addClass("disabled");
        _bsTooltipInit($lodge, {});
      }
    });
  }

  function _layoutItem(item, isRepeat, itemData) {
    var itemContainer = $("<div>"),
      childrenAnchorPoint;

    // if this is a repeatable item (such as a group), add repetitionIndex to item ID
    if (item.isRepeatable) {
      item.isRemovable = isRepeat;
    }

    if (itemData !== undefined && item.name in itemData) {
      item.value = itemData[item.name];
    } else {
      item.value = "";
    }

    if (item.type === "section" || item.type === "group") {
      item.isPreviewMode = true;
      itemContainer.append(Handlebars.templates[item.type](item));
      _initCollapsible(itemContainer);
    } else if (item.type === "radiobuttons" || item.type === "select") {
      var isSpecified = false;
      itemContainer.append(
        $("<label>").text(item.label).addClass("form-label")
      );
      $.each(item.options, function (index, option) {
        if (option.value === item.value) {
          itemContainer.append($("<p>").text(option.label));
          isSpecified = true;
        }
      });

      if (!isSpecified) {
        itemContainer.append($("<p>").text("Not specified"));
      }
    } else if (item.type === "checkbox") {
      if (item.value) {
        itemContainer.append($("<p>").text(item.label));
      }
    } else if (item.type === "declaration") {
      itemContainer.append(
        $("<label>").text(item.label).addClass("form-label")
      );
      itemContainer.append(
        $("<p>").text(
          item.value ? "Declaration checked" : "Declaration not checked"
        )
      );
    } else if (item.type === "file") {
      itemContainer.append(
        $("<label>").text(item.label).addClass("form-label")
      );
      if (item.value) {
        var fileLink = $("<a>")
          .attr("href", "#")
          .attr("role", "button")
          .click(function (e) {
            e.preventDefault();
          });
        fileLink.attr("href", item.value);
        fileLink.attr("target", "_blank");
        fileLink.text(item.value.substr(item.value.lastIndexOf("/") + 1));
        itemContainer.append($("<p>").append(fileLink));
      } else {
        itemContainer.append($("<p>").text("No file attached"));
      }
    } else if (item.type === "label") {
      itemContainer.append(
        $("<label>").text(item.label).addClass("form-label")
      );
    } else {
      itemContainer.append(
        $("<label>").text(item.label).addClass("form-label")
      );
      if (item.value) {
        itemContainer.append($("<p>").text(item.value));
      } else {
        itemContainer.append($("<p>").text("Not specified"));
      }
    }

    // unset item value if they were set otherwise there may be unintended consequences if extra form fields are created dynamically
    item.value = undefined;

    childrenAnchorPoint = _getCreateChildrenAnchorPoint(itemContainer);

    if (item.conditions !== undefined) {
      if (item.conditions !== undefined) {
        $.each(item.conditions, function (condition, children) {
          if (condition === itemData[item.name]) {
            $.each(children, function (childIndex, child) {
              _appendChild(child, childrenAnchorPoint, itemData);
            });
          }
        });
      }
    }

    if (item.children !== undefined) {
      $.each(item.children, function (childIndex, child) {
        _appendChild(child, childrenAnchorPoint, itemData);
      });
    }

    return itemContainer;
  }

  function _appendChild(child, childrenAnchorPoint, itemData) {
    if (child.isRepeatable) {
      var childData;
      if (itemData !== undefined) {
        childData = itemData[child.name][0];
      }
      childrenAnchorPoint.append(_layoutItem(child, false, childData));

      var repeatItemsAnchorPoint = $("<div>");
      childrenAnchorPoint.append(repeatItemsAnchorPoint);

      if (
        itemData !== undefined &&
        child.name in itemData &&
        itemData[child.name].length > 1
      ) {
        $.each(
          itemData[child.name].slice(1),
          function (childRepetitionIndex, repeatData) {
            repeatItemsAnchorPoint.append(_layoutItem(child, true, repeatData));
          }
        );
      }
    } else {
      childrenAnchorPoint.append(_layoutItem(child, false, itemData));
    }
  }

  function _getCreateChildrenAnchorPoint($itemContainer) {
    var $childrenAnchorPoint;

    // if no children anchor point was defined within the template, create one under current item
    if ($itemContainer.find(".children-anchor-point").length) {
      $childrenAnchorPoint = $itemContainer.find(".children-anchor-point");
    } else {
      $childrenAnchorPoint = $("<div>");
      // create as an expanded collapse so child items are visible by default
      $childrenAnchorPoint.addClass("children-anchor-point collapse show");
      $itemContainer.append($childrenAnchorPoint);
    }

    // If a children anchor point exists and uses the older BS3 'in' class,
    // normalize it to Bootstrap 5 'show' so it is visible by default.
    // Also ensure any collapse instance is shown.
    if ($childrenAnchorPoint && $childrenAnchorPoint.length) {
      // operate on the first match to avoid changing other instances
      $childrenAnchorPoint = $childrenAnchorPoint.first();
      if ($childrenAnchorPoint.hasClass("collapse")) {
        $childrenAnchorPoint.removeClass("in").addClass("show");
        if (typeof bootstrap !== "undefined" && bootstrap.Collapse) {
          try {
            var inst = bootstrap.Collapse.getOrCreateInstance(
              $childrenAnchorPoint.get(0)
            );
            if (inst && inst.show) inst.show();
          } catch (e) {
            // ignore if Collapse API not compatible
          }
        }
      }
    }

    return $childrenAnchorPoint;
  }

  function _initCollapsible($itemContainer) {
    var $collapsible = $itemContainer.find(".children-anchor-point").first(),
      $topLink = $collapsible.siblings(".collapse-link-top"),
      $topLinkSpan = $topLink.find("span"),
      $bottomLink = $collapsible.siblings(".collapse-link-bottom").first();

    $collapsible
      .on("hide.bs.collapse", function () {
        $topLinkSpan.removeClass("fa-chevron-down").addClass("fa-chevron-up");
        if ($bottomLink.length) {
          $bottomLink.hide();
        }
      })
      .on("show.bs.collapse", function () {
        $topLinkSpan.removeClass("fa-chevron-up").addClass("fa-chevron-down");
      })
      .on("shown.bs.collapse", function () {
        if ($bottomLink.length) {
          $bottomLink.show();
        }
      });

    $topLink.click(function () {
      if (typeof bootstrap !== "undefined" && bootstrap.Collapse) {
        bootstrap.Collapse.getOrCreateInstance($collapsible.get(0)).toggle();
      } else if ($collapsible.collapse) {
        $collapsible.collapse("toggle");
      }
    });

    if ($bottomLink.length) {
      $bottomLink.click(function () {
        if (typeof bootstrap !== "undefined" && bootstrap.Collapse) {
          bootstrap.Collapse.getOrCreateInstance($collapsible.get(0)).toggle();
        } else if ($collapsible.collapse) {
          $collapsible.collapse("toggle");
        }
      });
    }
  }

  return {
    layoutPreviewItems: function (
      containerSelector,
      formStructure,
      data,
      tempFilesUrl
    ) {
      var container = $(containerSelector);

      for (var i = 0; i < formStructure.length; i++) {
        var itemData;

        // ensure item data exists
        if (data && i < data.length) {
          itemData = data[i][formStructure[i].name][0];
        }

        container.append(_layoutItem(formStructure[i], false, itemData));
      }
    },
    initialiseSidebarMenu: function (sidebarMenuSelector) {
      $(".section").each(function (index, value) {
        var link = $("<a>")
          .attr("href", "#")
          .attr("role", "button")
          .click(function (e) {
            e.preventDefault();
          });
        link.attr("href", "#" + $(this).attr("id"));
        link.text($(this).text());
        $("#sectionList ul").append($("<li>").append(link));
      });

      var sectionList = $(sidebarMenuSelector);
      $("body").scrollspy({ target: "#sectionList" });
      sectionList.affix({ offset: { top: sectionList.offset().top } });
    },
    setupDisclaimer: _setupDisclaimers,
  };
});
