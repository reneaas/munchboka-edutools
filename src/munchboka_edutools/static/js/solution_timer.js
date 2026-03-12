(function () {
  const STORAGE_PREFIX = "munchboka-solution-timer-v2:";
  const DEFAULT_DELAY_SECONDS = 300;
  const VISIBILITY_THRESHOLD = 0.35;
  const UPDATE_INTERVAL_MS = 1000;

  const stateByElement = new Map();
  let activeModal = null;
  let modalElements = null;

  function getStorage() {
    try {
      return window.sessionStorage;
    } catch (_error) {
      return null;
    }
  }

  function storageKey(solutionId) {
    return `${STORAGE_PREFIX}${window.location.pathname}::${solutionId}`;
  }

  function readState(key) {
    const storage = getStorage();
    if (!storage) return {};

    try {
      const raw = storage.getItem(key);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_error) {
      return {};
    }
  }

  function writeState(key, value) {
    const storage = getStorage();
    if (!storage) return;

    try {
      storage.setItem(key, JSON.stringify(value));
    } catch (_error) {
      // Non-fatal: feature degrades to page-only behavior.
    }
  }

  function formatDuration(totalSeconds) {
    const seconds = Math.max(0, Math.floor(totalSeconds));
    const minutes = Math.floor(seconds / 60);
    const remainder = seconds % 60;

    if (minutes <= 0) {
      return `${remainder} sek`;
    }

    if (remainder === 0) {
      return `${minutes} min`;
    }

    return `${minutes} min ${remainder} s`;
  }

  function elapsedSeconds(entry) {
    if (!entry.state.startedAt) return 0;
    return Math.max(0, Math.floor((Date.now() - entry.state.startedAt) / 1000));
  }

  function remainingSeconds(entry) {
    return Math.max(0, entry.delaySeconds - elapsedSeconds(entry));
  }

  function isLocked(entry) {
    if (entry.delaySeconds <= 0) return false;
    if (entry.state.bypassed === true) return false;
    if (!entry.state.startedAt) return false;
    return remainingSeconds(entry) > 0;
  }

  function ensureStatusNode(entry) {
    if (entry.statusNode && entry.statusNode.isConnected) {
      return entry.statusNode;
    }

    const statusNode = document.createElement("div");
    statusNode.className = "solution-lock-status";
    statusNode.setAttribute("aria-live", "polite");
    entry.statusNode = statusNode;
    entry.titleNode.insertAdjacentElement("afterend", statusNode);
    return statusNode;
  }

  function updateStatus(entry) {
    const statusNode = ensureStatusNode(entry);
    const started = Boolean(entry.state.startedAt);

    if (isLocked(entry)) {
      entry.element.classList.add("solution-soft-locked");
      statusNode.hidden = false;
      statusNode.textContent = `Løsningen åpnes om ${formatDuration(remainingSeconds(entry))}.`;
      return;
    }

    entry.element.classList.remove("solution-soft-locked");
    if (!started && entry.delaySeconds > 0) {
      statusNode.hidden = false;
      statusNode.textContent = `Løsningen blir tilgjengelig ${formatDuration(entry.delaySeconds)} etter at du har sett oppgaven.`;
      return;
    }

    statusNode.hidden = true;
    statusNode.textContent = "";
  }

  function ensureStarted(entry) {
    if (entry.delaySeconds <= 0 || entry.state.startedAt) {
      return;
    }

    entry.state.startedAt = Date.now();
    writeState(entry.storageKey, entry.state);
    updateStatus(entry);
    updateModal();
  }

  function openSolution(entry) {
    if (!entry.titleNode) return;
    window.setTimeout(() => {
      entry.titleNode.dispatchEvent(
        new MouseEvent("click", { bubbles: true, cancelable: true, view: window })
      );
    }, 0);
  }

  function closeModal() {
    if (!modalElements) return;
    modalElements.backdrop.hidden = true;
    activeModal = null;
  }

  function ensureModal() {
    if (modalElements) {
      return modalElements;
    }

    const backdrop = document.createElement("div");
    backdrop.className = "solution-lock-modal-backdrop";
    backdrop.hidden = true;

    const dialog = document.createElement("div");
    dialog.className = "solution-lock-modal";
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-labelledby", "solution-lock-modal-title");

    dialog.innerHTML = `
      <h3 id="solution-lock-modal-title">Vent litt med løsningen</h3>
      <p class="solution-lock-modal-text">
        Du har bare prøvd på oppgaven i <strong data-role="tried"></strong>.
        Du bør gi deg selv <strong data-role="remaining"></strong> til på å prøve først før du ser på løsningen.
      </p>
      <p class="solution-lock-modal-countdown" data-role="countdown"></p>
      <div class="solution-lock-modal-actions">
        <button type="button" class="solution-lock-modal-button secondary" data-action="cancel">Fortsett å prøve</button>
        <button type="button" class="solution-lock-modal-button primary" data-action="override">Vis løsning nå</button>
      </div>
    `;

    backdrop.appendChild(dialog);
    document.body.appendChild(backdrop);

    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) {
        closeModal();
      }
    });

    dialog.querySelector("[data-action='cancel']").addEventListener("click", () => {
      closeModal();
    });

    dialog.querySelector("[data-action='override']").addEventListener("click", () => {
      if (!activeModal) return;
      activeModal.state.bypassed = true;
      writeState(activeModal.storageKey, activeModal.state);
      updateStatus(activeModal);
      closeModal();
      openSolution(activeModal);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && activeModal) {
        closeModal();
      }
    });

    modalElements = {
      backdrop,
      tried: dialog.querySelector("[data-role='tried']"),
      remaining: dialog.querySelector("[data-role='remaining']"),
      countdown: dialog.querySelector("[data-role='countdown']"),
    };

    return modalElements;
  }

  function updateModal() {
    if (!activeModal || !modalElements) return;

    const tried = elapsedSeconds(activeModal);
    const remaining = remainingSeconds(activeModal);

    if (!isLocked(activeModal)) {
      closeModal();
      openSolution(activeModal);
      return;
    }

    modalElements.tried.textContent = formatDuration(tried);
    modalElements.remaining.textContent = formatDuration(remaining);
    modalElements.countdown.textContent = `Nedtelling: ${formatDuration(remaining)}`;
  }

  function openModal(entry) {
    ensureModal();
    activeModal = entry;
    modalElements.backdrop.hidden = false;
    updateModal();
  }

  function handleLockedClick(entry, event) {
    if (entry.delaySeconds > 0 && !entry.state.startedAt) {
      ensureStarted(entry);
    }

    if (!isLocked(entry)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
    openModal(entry);
  }

  function isToggleTrigger(target, root) {
    if (!(target instanceof Element)) {
      return false;
    }

    const trigger = target.closest(".admonition-title, .toggle-button");
    return Boolean(trigger && root.contains(trigger));
  }

  function registerSolution(element) {
    const titleNode = element.querySelector(":scope > .admonition-title");
    if (!titleNode) return;

    const delayClass = Array.from(element.classList).find((className) =>
      className.startsWith("solution-delay-")
    );
    const refClass = Array.from(element.classList).find((className) =>
      className.startsWith("solution-ref-")
    );

    const solutionId =
      (refClass ? refClass.replace("solution-ref-", "") : null) ||
      element.dataset.solutionId ||
      element.id ||
      `solution-${stateByElement.size + 1}`;
    const delaySeconds = Number.parseInt(
      (delayClass ? delayClass.replace("solution-delay-", "") : null) ||
        element.dataset.delaySeconds ||
        `${DEFAULT_DELAY_SECONDS}`,
      10
    );
    const key = storageKey(solutionId);

    const entry = {
      element,
      titleNode,
      statusNode: null,
      solutionId,
      delaySeconds: Number.isFinite(delaySeconds) ? delaySeconds : DEFAULT_DELAY_SECONDS,
      storageKey: key,
      state: readState(key),
    };

    stateByElement.set(element, entry);
    element.addEventListener(
      "click",
      (event) => {
        if (!isToggleTrigger(event.target, element)) {
          return;
        }

        handleLockedClick(entry, event);
      },
      true
    );

    element.addEventListener(
      "keydown",
      (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }

        if (!isToggleTrigger(event.target, element)) {
          return;
        }

        handleLockedClick(entry, event);
      },
      true
    );
    updateStatus(entry);
  }

  function observeSolutions() {
    const entries = Array.from(stateByElement.values());
    if (entries.length === 0) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      entries.forEach((entry) => ensureStarted(entry));
      return;
    }

    const observer = new IntersectionObserver(
      (observerEntries) => {
        observerEntries.forEach((observerEntry) => {
          if (!observerEntry.isIntersecting) return;
          if (observerEntry.intersectionRatio < VISIBILITY_THRESHOLD) return;
          const entry = stateByElement.get(observerEntry.target);
          if (!entry) return;
          ensureStarted(entry);
          observer.unobserve(observerEntry.target);
        });
      },
      {
        threshold: [VISIBILITY_THRESHOLD],
      }
    );

    entries.forEach((entry) => observer.observe(entry.element));
  }

  function tick() {
    stateByElement.forEach((entry) => updateStatus(entry));
    updateModal();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".admonition.solution.solution-timed").forEach(registerSolution);
    observeSolutions();
    window.setInterval(tick, UPDATE_INTERVAL_MS);
  });
})();