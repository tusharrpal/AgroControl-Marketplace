(() => {
    const progress = document.querySelector("[data-page-progress]");

    const showProgress = () => progress?.classList.add("is-visible");
    const hideProgress = () => progress?.classList.remove("is-visible");

    window.addEventListener("pageshow", hideProgress);

    document.addEventListener("click", (event) => {
        const link = event.target.closest("a[href]");
        if (
            !link ||
            event.defaultPrevented ||
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey ||
            link.target === "_blank" ||
            link.hasAttribute("download")
        ) {
            return;
        }

        const destination = new URL(link.href, window.location.href);
        if (
            destination.origin === window.location.origin &&
            destination.href !== window.location.href &&
            !destination.hash
        ) {
            showProgress();
        }
    });

    document.addEventListener("submit", (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || form.dataset.noLoading !== undefined) {
            return;
        }

        const submitter = event.submitter;
        if (submitter instanceof HTMLButtonElement) {
            submitter.disabled = true;
            submitter.setAttribute("aria-busy", "true");
            const original = submitter.innerHTML;
            submitter.dataset.originalContent = original;
            submitter.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Working…';
        }
        showProgress();
    });
})();
