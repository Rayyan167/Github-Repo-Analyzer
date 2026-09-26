from django.contrib import admin

from .models import RepositoryAnalysis


@admin.register(RepositoryAnalysis)
class RepositoryAnalysisAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'score', 'stars', 'open_issues', 'analyzed_at')
    list_filter = ('language',)
    search_fields = ('owner', 'repo_name')
    ordering = ('-analyzed_at',)
    readonly_fields = ('analyzed_at',)
