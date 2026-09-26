"""
The health-scoring logic for a repository.

Every check below is a plain function that looks at data we already fetched
from GitHub and returns a small dict describing the result. There is no
machine learning and no hidden logic — each function is a handful of
if/else statements, so the score is easy to explain: "add up the points
from each check that passed."

The seven checks add up to a maximum of 100 points:
    README              15
    License              10
    Documentation        15
    Tests                15
    Recent Activity      20
    Repository Size      10
    Issues               15
    ------------------------
    Total               100
"""

from datetime import datetime, timezone

TEST_FOLDER_NAMES = {'tests', 'test', 'spec', '__tests__'}
DOC_FOLDER_NAMES = {'docs', 'doc', 'documentation'}

LARGE_REPO_SIZE_KB = 500_000  # ~500 MB, checked out size on GitHub's side


def _root_names(contents):
    """Return the lowercase names of everything in the repository root."""
    return {item.get('name', '').lower() for item in contents}


def check_readme(contents):
    names = _root_names(contents)
    has_readme = any(name.startswith('readme') for name in names)

    if has_readme:
        return {
            'name': 'README',
            'status': 'pass',
            'icon': '✅',
            'message': 'Repository contains a README file.',
            'points': 15,
            'max_points': 15,
        }
    return {
        'name': 'README',
        'status': 'fail',
        'icon': '❌',
        'message': 'No README file was found in the repository root.',
        'points': 0,
        'max_points': 15,
    }


def check_license(repo_data):
    license_info = repo_data.get('license')

    if license_info and license_info.get('name'):
        return {
            'name': 'License',
            'status': 'pass',
            'icon': '✅',
            'message': f"Licensed under {license_info['name']}.",
            'points': 10,
            'max_points': 10,
        }
    return {
        'name': 'License',
        'status': 'fail',
        'icon': '❌',
        'message': 'No open-source license was detected.',
        'points': 0,
        'max_points': 10,
    }


def check_documentation(contents):
    names = _root_names(contents)
    has_readme = any(name.startswith('readme') for name in names)
    has_docs_folder = any(name in DOC_FOLDER_NAMES for name in names)
    has_contributing = any(name.startswith('contributing') for name in names)

    if has_docs_folder or has_contributing:
        return {
            'name': 'Documentation',
            'status': 'pass',
            'icon': '✅',
            'message': 'Repository has additional documentation (a docs folder or a contribution guide).',
            'points': 15,
            'max_points': 15,
        }
    if has_readme:
        return {
            'name': 'Documentation',
            'status': 'warning',
            'icon': '⚠️',
            'message': 'Only a README was found — no dedicated docs folder or contribution guide.',
            'points': 7,
            'max_points': 15,
        }
    return {
        'name': 'Documentation',
        'status': 'fail',
        'icon': '❌',
        'message': 'No documentation was detected.',
        'points': 0,
        'max_points': 15,
    }


def check_tests(contents):
    names = _root_names(contents)
    has_tests = any(name in TEST_FOLDER_NAMES for name in names) or any(
        name.startswith('test_') or name.startswith('test.') for name in names
    )

    if has_tests:
        return {
            'name': 'Tests',
            'status': 'pass',
            'icon': '✅',
            'message': 'A tests folder or test files were found in the repository root.',
            'points': 15,
            'max_points': 15,
        }
    return {
        'name': 'Tests',
        'status': 'warning',
        'icon': '⚠️',
        'message': 'Could not clearly identify tests. They may still exist deeper in the project.',
        'points': 0,
        'max_points': 15,
    }


def check_recent_activity(repo_data):
    pushed_at = repo_data.get('pushed_at')

    if not pushed_at:
        return {
            'name': 'Recent Activity',
            'status': 'warning',
            'icon': '⚠️',
            'message': 'Could not determine when the repository was last updated.',
            'points': 0,
            'max_points': 20,
        }

    last_push = datetime.strptime(pushed_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    days_since = (datetime.now(timezone.utc) - last_push).days

    if days_since <= 90:
        return {
            'name': 'Recent Activity',
            'status': 'pass',
            'icon': '✅',
            'message': f'Repository was updated {days_since} day(s) ago.',
            'points': 20,
            'max_points': 20,
        }
    if days_since <= 365:
        return {
            'name': 'Recent Activity',
            'status': 'warning',
            'icon': '⚠️',
            'message': f'Repository was last updated {days_since} days ago — activity has slowed.',
            'points': 10,
            'max_points': 20,
        }
    return {
        'name': 'Recent Activity',
        'status': 'fail',
        'icon': '❌',
        'message': f'Repository has not been updated in over a year ({days_since} days).',
        'points': 0,
        'max_points': 20,
    }


def check_repository_size(repo_data):
    size_kb = repo_data.get('size', 0)

    if size_kb == 0:
        return {
            'name': 'Repository Size',
            'status': 'warning',
            'icon': '⚠️',
            'message': 'Repository appears to be empty.',
            'points': 0,
            'max_points': 10,
        }
    if size_kb > LARGE_REPO_SIZE_KB:
        return {
            'name': 'Repository Size',
            'status': 'warning',
            'icon': '⚠️',
            'message': 'Repository is very large, which can make it harder to maintain and clone.',
            'points': 5,
            'max_points': 10,
        }
    return {
        'name': 'Repository Size',
        'status': 'pass',
        'icon': '✅',
        'message': 'Repository size looks normal.',
        'points': 10,
        'max_points': 10,
    }


def check_issues(repo_data):
    open_issues = repo_data.get('open_issues_count', 0)

    if open_issues <= 50:
        return {
            'name': 'Issues',
            'status': 'pass',
            'icon': '✅',
            'message': f'{open_issues} open issue(s) — a manageable amount.',
            'points': 15,
            'max_points': 15,
        }
    if open_issues <= 200:
        return {
            'name': 'Issues',
            'status': 'warning',
            'icon': '⚠️',
            'message': f'{open_issues} open issues. This is on the higher side.',
            'points': 8,
            'max_points': 15,
        }
    return {
        'name': 'Issues',
        'status': 'warning',
        'icon': '⚠️',
        'message': f'{open_issues} open issues. Many open issues may indicate limited maintenance capacity.',
        'points': 0,
        'max_points': 15,
    }


# Maps a check's name to the suggestion shown when that check is not a full pass.
SUGGESTION_MESSAGES = {
    'README': 'Add a README explaining installation, usage, and contribution.',
    'License': 'Consider adding an open-source license so others know how they can use the project.',
    'Documentation': 'Add a docs folder or a CONTRIBUTING guide to help new contributors.',
    'Tests': 'Add or improve automated tests to catch regressions early.',
    'Recent Activity': 'Keep the codebase and its dependencies updated with regular commits.',
    'Repository Size': 'Review whether large files or build artifacts should be excluded from version control.',
    'Issues': 'Reduce unresolved issues by triaging and closing outdated ones.',
}


def build_suggestions(checks):
    """Turn any non-passing check into a plain-language suggestion."""
    suggestions = []
    for check in checks:
        if check['status'] != 'pass':
            suggestion = SUGGESTION_MESSAGES.get(check['name'])
            if suggestion:
                suggestions.append(suggestion)
    return suggestions


def calculate_health(repo_data, contents):
    """Run every check and return the overall score, checks, and suggestions.

    `repo_data` is the dict returned by github_service.get_repository().
    `contents` is the list returned by github_service.get_root_contents().
    """
    checks = [
        check_readme(contents),
        check_license(repo_data),
        check_documentation(contents),
        check_tests(contents),
        check_recent_activity(repo_data),
        check_repository_size(repo_data),
        check_issues(repo_data),
    ]

    score = sum(check['points'] for check in checks)

    return {
        'score': score,
        'checks': checks,
        'suggestions': build_suggestions(checks),
    }
