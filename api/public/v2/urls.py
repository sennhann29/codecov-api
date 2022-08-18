from django.conf import settings, urls
from django.urls import include, path
from rest_framework.exceptions import server_error

from api.shared.error_views import not_found
from utils.routers import OptionalTrailingSlashRouter, RetrieveUpdateDestroyRouter

from .branch.views import BranchViewSet
from .commit.views import CommitsViewSet
from .compare.views import CompareViewSet
from .coverage.views import CoverageViewSet
from .owner.views import OwnerViewSet, UserViewSet
from .pull.views import PullViewSet
from .repo.views import RepositoryViewSet

urls.handler404 = not_found
urls.handler500 = server_error


owners_router = OptionalTrailingSlashRouter()
owners_router.register(r"", OwnerViewSet, basename="api-v2-owners")

owner_artifacts_router = OptionalTrailingSlashRouter()
owner_artifacts_router.register(r"users", UserViewSet, basename="api-v2-users")

repository_router = OptionalTrailingSlashRouter()
repository_router.register(r"repos", RepositoryViewSet, basename="api-v2-repos")

repository_artifacts_router = OptionalTrailingSlashRouter()
repository_artifacts_router.register(r"pulls", PullViewSet, basename="api-v2-pulls")
repository_artifacts_router.register(
    r"commits", CommitsViewSet, basename="api-v2-commits"
)
repository_artifacts_router.register(
    r"branches", BranchViewSet, basename="api-v2-branches"
)

compare_router = RetrieveUpdateDestroyRouter()
compare_router.register(r"compare", CompareViewSet, basename="api-v2-compare")

coverage_router = OptionalTrailingSlashRouter()
coverage_router.register(r"coverage", CoverageViewSet, basename="api-v2-coverage")

service_prefix = "<str:service>/"
owner_prefix = "<str:service>/<str:owner_username>/"
repo_prefix = "<str:service>/<str:owner_username>/repos/<str:repo_name>/"
flag_prefix = (
    "<str:service>/<str:owner_username>/repos/<str:repo_name>/flags/<str:flag_name>/"
)

urlpatterns = [
    path(service_prefix, include(owners_router.urls)),
    path(owner_prefix, include(owner_artifacts_router.urls)),
    path(owner_prefix, include(repository_router.urls)),
    path(repo_prefix, include(repository_artifacts_router.urls)),
    path(repo_prefix, include(compare_router.urls)),
]

if settings.TIMESERIES_ENABLED:
    urlpatterns += [
        path(repo_prefix, include(coverage_router.urls)),
        path(flag_prefix, include(coverage_router.urls)),
    ]
