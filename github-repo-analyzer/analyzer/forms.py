import re

from django import forms

# Matches URLs like:
#   https://github.com/django/django
#   http://www.github.com/django/django
#   github.com/django/django
#   https://github.com/django/django.git
#   https://github.com/django/django/
GITHUB_URL_PATTERN = re.compile(
    r'^(?:https?://)?(?:www\.)?github\.com/'
    r'(?P<owner>[A-Za-z0-9_.-]+)/'
    r'(?P<repo>[A-Za-z0-9_.-]+?)'
    r'(?:\.git)?/?$'
)


class RepositoryURLForm(forms.Form):
    """A single-field form for the GitHub repository URL on the home page."""

    repo_url = forms.CharField(
        label='GitHub Repository URL',
        max_length=500,
        widget=forms.TextInput(attrs={
            'placeholder': 'https://github.com/django/django',
            'class': 'url-input',
            'autofocus': True,
            'autocomplete': 'off',
        }),
    )

    def clean_repo_url(self):
        url = self.cleaned_data['repo_url'].strip()
        match = GITHUB_URL_PATTERN.match(url)

        if not match:
            raise forms.ValidationError(
                "That doesn't look like a valid GitHub repository URL. "
                "Try something like https://github.com/owner/repository"
            )

        # Stash the parsed owner/repo so the view doesn't have to
        # re-parse the URL.
        self.cleaned_data['owner'] = match.group('owner')
        self.cleaned_data['repo'] = match.group('repo')
        return url
