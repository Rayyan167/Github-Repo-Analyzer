document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('analyze-form');
    var button = document.getElementById('analyze-btn');
    var input = document.getElementById('id_repo_url');

    // Show a simple loading state while the analysis request is in flight.
    // The page does a normal full-page submit (no AJAX) — this just gives
    // the user feedback that something is happening, since a real analysis
    // involves a few GitHub API calls and can take a couple of seconds.
    if (form && button) {
        form.addEventListener('submit', function () {
            button.disabled = true;
            button.classList.add('is-loading');
            var label = button.querySelector('.btn-text');
            if (label) {
                label.textContent = 'Analyzing...';
            }
        });
    }

    // "Try: django/django" style quick-fill buttons on the home page.
    var hintLinks = document.querySelectorAll('.hint-link');
    hintLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            if (input) {
                input.value = link.getAttribute('data-repo');
                input.focus();
            }
        });
    });
});
