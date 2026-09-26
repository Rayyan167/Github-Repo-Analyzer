from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime

from . import github_service, health_score
from .forms import RepositoryURLForm
from .models import RepositoryAnalysis


def home(request):
    """Landing page: shows the URL form, and runs the analysis on submit.

    Uses the "POST, then redirect to a GET page" pattern: a successful
    analysis redirects to the dashboard page for that result, instead of
    rendering it directly. That way, reloading the results page (or hitting
    the back button) never re-runs the analysis by accident.
    """
    if request.method == 'POST':
        form = RepositoryURLForm(request.POST)

        if form.is_valid():
            owner = form.cleaned_data['owner']
            repo = form.cleaned_data['repo']

            try:
                analysis = _analyze_repository(owner, repo)
            except github_service.GitHubAPIError as error:
                messages.error(request, str(error))
                return render(request, 'analyzer/home.html', {'form': form})

            return redirect('analyzer:dashboard', pk=analysis.pk)
    else:
        form = RepositoryURLForm()

    return render(request, 'analyzer/home.html', {'form': form})


def _analyze_repository(owner, repo):
    """Fetch data from GitHub, score it, save it, and return the saved row.

    This is the one place that ties the GitHub service and the scoring
    logic together. It can raise any of the exceptions defined in
    github_service (all subclasses of GitHubAPIError); the caller is
    expected to handle those.
    """
    repo_data = github_service.get_repository(owner, repo)
    contents = github_service.get_root_contents(owner, repo)
    commits = github_service.get_recent_commits(owner, repo)

    result = health_score.calculate_health(repo_data, contents)

    license_info = repo_data.get('license')
    license_name = license_info.get('name') if license_info else None

    pushed_at = repo_data.get('pushed_at')
    repo_last_updated = parse_datetime(pushed_at) if pushed_at else None

    owner_info = repo_data.get('owner') or {}

    analysis = RepositoryAnalysis.objects.create(
        repo_url=repo_data.get('html_url') or f'https://github.com/{owner}/{repo}',
        owner=owner_info.get('login', owner),
        repo_name=repo_data.get('name', repo),
        description=repo_data.get('description') or '',
        stars=repo_data.get('stargazers_count', 0),
        forks=repo_data.get('forks_count', 0),
        open_issues=repo_data.get('open_issues_count', 0),
        language=repo_data.get('language') or '',
        license_name=license_name,
        repo_last_updated=repo_last_updated,
        score=result['score'],
        checks=result['checks'],
        suggestions=result['suggestions'],
        recent_commit_count=len(commits),
    )
    return analysis


def dashboard(request, pk):
    """Show the health report for one saved analysis."""
    analysis = get_object_or_404(RepositoryAnalysis, pk=pk)
    return render(request, 'analyzer/dashboard.html', {'analysis': analysis})


def history(request):
    """List every past analysis, most recent first, with simple pagination."""
    all_analyses = RepositoryAnalysis.objects.all()
    paginator = Paginator(all_analyses, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'analyzer/history.html', {'page_obj': page_obj})
