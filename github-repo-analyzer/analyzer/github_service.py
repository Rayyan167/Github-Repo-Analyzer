"""
A small, intentionally simple wrapper around the parts of the GitHub REST
API that this project needs.

There is no "client class" with lots of abstraction here on purpose — just a
handful of functions that each do one clear thing. Every function either
returns plain Python data (dicts/lists straight from GitHub's JSON) or raises
one of the exceptions below, so callers only have to handle a few cases.
"""

import requests
from django.conf import settings


class GitHubAPIError(Exception):
    """Base exception for anything that goes wrong talking to GitHub."""


class RepositoryNotFoundError(GitHubAPIError):
    """Raised when the repository doesn't exist or is private."""


class RateLimitExceededError(GitHubAPIError):
    """Raised when GitHub's rate limit has been hit."""


REQUEST_TIMEOUT_SECONDS = 10


def _get_headers():
    """Build the headers used for every request.

    If GITHUB_TOKEN is set in the environment, we send it along to raise
    the rate limit from 60 to 5,000 requests/hour. It is entirely optional.
    """
    headers = {'Accept': 'application/vnd.github+json'}
    if settings.GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {settings.GITHUB_TOKEN}'
    return headers


def _get(url):
    """Perform a GET request and translate common problems into our
    own exceptions, so views don't need to know about requests/HTTP details.
    """
    try:
        response = requests.get(url, headers=_get_headers(), timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        raise GitHubAPIError('The request to GitHub timed out. Please try again.')
    except requests.exceptions.RequestException:
        raise GitHubAPIError('Could not reach GitHub. Check your internet connection and try again.')

    if response.status_code == 404:
        raise RepositoryNotFoundError(
            'Repository not found. Check the URL and make sure the repository is public.'
        )

    if response.status_code == 403 and response.headers.get('X-RateLimit-Remaining') == '0':
        raise RateLimitExceededError(
            "GitHub's API rate limit has been reached for this server. "
            "Please try again in a few minutes, or add a GITHUB_TOKEN to raise the limit."
        )

    if response.status_code >= 400:
        raise GitHubAPIError(f'GitHub API returned an unexpected error (status {response.status_code}).')

    return response


def get_repository(owner, repo):
    """Fetch the main repository record, e.g. GET /repos/{owner}/{repo}.

    Returns a dict with keys like 'name', 'description', 'stargazers_count',
    'forks_count', 'open_issues_count', 'language', 'license', 'pushed_at',
    'html_url', 'size', and 'owner'.
    """
    url = f'{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}'
    response = _get(url)
    return response.json()


def get_root_contents(owner, repo):
    """Fetch the list of files/folders in the repository root.

    Used to look for a README, tests folder, docs folder, etc. Returns an
    empty list for an empty repository instead of raising, since an empty
    repo is a perfectly valid (if unhealthy) thing to analyze.
    """
    url = f'{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents'
    try:
        response = _get(url)
    except RepositoryNotFoundError:
        return []

    data = response.json()
    return data if isinstance(data, list) else []


def get_recent_commits(owner, repo, count=10):
    """Fetch up to `count` of the most recent commits on the default branch.

    Returns an empty list if commits can't be read (e.g. an empty repo),
    rather than failing the whole analysis over a "nice to have" detail.
    """
    url = f'{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/commits?per_page={count}'
    try:
        response = _get(url)
    except GitHubAPIError:
        return []

    data = response.json()
    return data if isinstance(data, list) else []
