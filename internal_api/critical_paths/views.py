import asyncio

from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from services.decorators import torngit_safe
from services.archive import ReportService

from internal_api.compare.serializers import ComparisonSerializer
from internal_api.mixins import CompareSlugMixin
from internal_api.permissions import RepositoryArtifactPermissions

from services.repo_providers import RepoProviderService

from core.models import Commit

class CriticalPathViewSet(CompareSlugMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    # TODO: this is placeholder.. to create cpc report serialzr
    serializer_class = ComparisonSerializer

    permission_classes = [RepositoryArtifactPermissions]
    
    # should probably bake query param into route using action decorator for
    # better self-documentation.. eh later
    @torngit_safe
    def retrieve(self, request, *args, **kwargs):
        if not request.query_params or not request.query_params["sha"]:
            raise APIException("You must include 'sha' query parameter")

        sha = request.query_params["sha"]
        commit = Commit.objects.get(commitid=sha)
        
        report_svc = ReportService()
        response = {}

        # Fetch critical paths so we know which files to focus on
        cpc_report = report_svc.build_critical_path_report_from_commit(commit)

        for critical_file_path in cpc_report.keys():
            response[critical_file_path] = []
            
            # src will contain a list containing each line of the file
            # will want to do some local caching
            src = str(
                asyncio.run(
                    RepoProviderService().get_adapter(
                        user=self.request.user,
                        repo=commit.repository
                    ).get_source(critical_file_path, sha)
                )["content"], 'utf-8'
            ).splitlines()

            critical_lines = cpc_report[critical_file_path]
            for i, txt in enumerate(src):
                response[critical_file_path].append({
                    "text": txt,
                    "is_critical": str(i+1) in critical_lines,
                    "is_covered": False # (to be updated if True..)
                })

        # check coverage report to see which ones are covered
        # maybe a cleaner way to do this
        cov_report = report_svc.build_report_from_commit(commit)
        files = sorted(cov_report.file_reports(), key=lambda x: x.name)
        for file in files:
            for line in file.lines:
                if file.name in response and isinstance(line[1].coverage, int) and line[1].coverage > 0:
                    response[file.name][line[0]]["is_covered"] = True

        # do properly with serializers
        return Response(
            data=response,
            status=200
        )