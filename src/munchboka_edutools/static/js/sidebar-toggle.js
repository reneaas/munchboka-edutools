(function () {
  "use strict";

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  function disposeTooltip(button) {
    button.removeAttribute("data-bs-toggle");
    button.removeAttribute("data-bs-placement");
    button.removeAttribute("data-bs-original-title");
    button.removeAttribute("aria-describedby");

    if (window.bootstrap && window.bootstrap.Tooltip) {
      var tooltip = window.bootstrap.Tooltip.getInstance(button);
      if (tooltip) {
        tooltip.dispose();
      }
    }
  }

  function installToggle(selector, checkboxId, sidebarSelector, fallbackLabel) {
    var buttons = document.querySelectorAll(selector);

    buttons.forEach(function (button) {
      var label = button.getAttribute("aria-label") || button.getAttribute("title") || fallbackLabel;

      button.setAttribute("aria-label", label);
      button.removeAttribute("title");
      disposeTooltip(button);

      if (button.dataset.munchbokaSidebarToggle === "1") {
        return;
      }

      button.dataset.munchbokaSidebarToggle = "1";
      button.addEventListener(
        "click",
        function (event) {
          var checkbox = document.getElementById(checkboxId);
          var sidebar = document.querySelector(sidebarSelector);

          if (!checkbox) {
            return;
          }

          event.preventDefault();
          event.stopImmediatePropagation();

          checkbox.checked = !checkbox.checked;
          checkbox.dispatchEvent(new Event("change", { bubbles: true }));

          if (checkbox.checked && sidebar) {
            var focusTarget = sidebar.querySelector(
              'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusTarget) {
              window.setTimeout(function () {
                focusTarget.focus({ preventScroll: true });
              }, 100);
            }
          } else {
            button.focus({ preventScroll: true });
          }
        },
        true
      );
    });
  }

  function installSidebarToggles() {
    installToggle(
      ".primary-toggle",
      "pst-primary-sidebar-checkbox",
      ".bd-sidebar-primary",
      "Toggle primary sidebar"
    );
    installToggle(
      ".secondary-toggle",
      "pst-secondary-sidebar-checkbox",
      ".bd-sidebar-secondary",
      "Toggle secondary sidebar"
    );
  }

  onReady(installSidebarToggles);
  window.addEventListener("load", installSidebarToggles, { once: true });
})();
