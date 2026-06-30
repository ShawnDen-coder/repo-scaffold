"""Thin PyGithub wrapper used by the gh-init orchestrator (and its tests).

Isolating the SDK behind ``GhInitClient`` lets the orchestrator depend on a
small, mockable surface instead of ``github`` module internals, and lets the
generated tests swap the whole client out without monkey-patching the SDK.
"""

from __future__ import annotations

from github import Auth
from github import Github
from github import GithubException
from github.Repository import Repository


class GhInitClient:
    """Tiny PyGithub wrapper that orchestrator and tests both consume."""

    def __init__(self, token: str):
        """Construct a client backed by the given personal access token."""
        self._gh = Github(auth=Auth.Token(token))
        self._user_login: str | None = None

    def authenticated_login(self) -> str:
        """Return the login of the token's user. Raises on a bad token."""
        if self._user_login is None:
            self._user_login = self._gh.get_user().login
        return self._user_login

    def get_or_create_repo(
        self,
        owner: str | None,
        name: str,
        *,
        description: str,
        private: bool,
        allow_existing: bool,
    ) -> Repository:
        """Create the repo on the right account, or look it up if already there."""
        login = self.authenticated_login()
        target_owner = owner or login
        try:
            if not owner or owner == login:
                user = self._gh.get_user()
                return user.create_repo(
                    name=name,
                    description=description or "",
                    private=private,
                    auto_init=False,
                )
            org = self._gh.get_organization(owner)
            return org.create_repo(
                name=name,
                description=description or "",
                private=private,
                auto_init=False,
            )
        except GithubException as exc:
            if exc.status == 422 and allow_existing:
                return self._gh.get_repo(f"{target_owner}/{name}")
            raise

    def set_secret(self, repo: Repository, name: str, value: str) -> None:
        """Create or replace an Actions secret. ``create_secret`` is PUT-based."""
        repo.create_secret(name, value)

    def set_variable(self, repo: Repository, name: str, value: str) -> None:
        """Create an Actions variable, falling back to ``edit`` if it exists."""
        try:
            repo.create_variable(name, value)
        except GithubException as exc:
            if exc.status in (409, 422):
                repo.get_variable(name).edit(value=value)
                return
            raise

    def set_homepage(self, repo: Repository, url: str) -> None:
        """Point the repository's ``Website`` field at the docs URL."""
        repo.edit(homepage=url)

    def enable_pages(self, repo: Repository, branch: str, path: str = "/") -> None:
        """Configure GitHub Pages to deploy from ``branch``/``path``.

        PyGithub 2.x has no Pages helper, so this calls the REST API directly:
        ``POST .../pages`` to create the site, falling back to ``PUT`` to update
        the source when a site already exists.
        """
        source = {"branch": branch, "path": path}
        try:
            repo.requester.requestJsonAndCheck("POST", f"{repo.url}/pages", input={"source": source})
        except GithubException as exc:
            if exc.status in (409, 422):
                repo.requester.requestJsonAndCheck("PUT", f"{repo.url}/pages", input={"source": source})
                return
            raise

    def protect_branch(self, repo: Repository, branch: str) -> None:
        """Enable branch protection on ``branch`` (requires admin on the repo).

        Rules are intentionally compatible with the generated ``version-bump``
        workflow: ``enforce_admins`` is left off so the release token (owned by
        a repo admin) can still push ``chore(version):`` commits and tags
        directly. Branch protection is unavailable on private repos without a
        paid GitHub plan; such a failure surfaces to the caller.
        """
        repo.get_branch(branch).edit_protection(
            required_approving_review_count=1,
            enforce_admins=False,
            allow_force_pushes=False,
            allow_deletions=False,
        )
