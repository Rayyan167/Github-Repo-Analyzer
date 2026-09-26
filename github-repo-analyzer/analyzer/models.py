from django.db import models


class RepositoryAnalysis(models.Model):
    """
    Stores the result of analyzing one GitHub repository at one point in time.

    We store the health checks and suggestions as JSON (instead of separate
    tables) because they are simple, read-only lists that belong to a single
    analysis. This keeps the database schema small and easy to reason about,
    and it means the history page can show a past result again without
    calling the GitHub API a second time.
    """

    # --- Where the repository lives -----------------------------------
    repo_url = models.URLField(max_length=500)
    owner = models.CharField(max_length=255)
    repo_name = models.CharField(max_length=255)

    # --- Basic repository information -----------------------------------
    description = models.TextField(blank=True, null=True)
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    open_issues = models.IntegerField(default=0)
    language = models.CharField(max_length=100, blank=True, null=True)
    license_name = models.CharField(max_length=150, blank=True, null=True)
    repo_last_updated = models.DateTimeField(blank=True, null=True)

    # --- Health analysis results -----------------------------------
    score = models.IntegerField(default=0)
    checks = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    recent_commit_count = models.IntegerField(default=0)

    # --- Bookkeeping -----------------------------------
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-analyzed_at']
        verbose_name_plural = 'Repository analyses'

    def __str__(self):
        return f'{self.full_name} ({self.score}/100)'

    @property
    def full_name(self):
        """e.g. 'django/django' — handy for templates and the admin list."""
        return f'{self.owner}/{self.repo_name}'
