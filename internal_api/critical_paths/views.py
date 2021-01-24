import asyncio

from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from services.decorators import torngit_safe
from services.archive import ReportService

from internal_api.compare.serializers import ComparisonSerializer
from internal_api.mixins import RepoPropertyMixin
from internal_api.permissions import RepositoryArtifactPermissions

from services.repo_providers import RepoProviderService

from core.models import Commit

from .serializers import (
    CriticalPathLine,
    CriticalPathFile,
    CriticalPathResponse,
    CriticalPathLineSerializer,
    CriticalPathFile,
    CriticalPathResponseSerializer
)

class CriticalPathViewSet(RepoPropertyMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    permission_classes = [RepositoryArtifactPermissions]
    
    # should probably bake query param into route using action decorator for
    # better self-documentation.. eh later
    def retrieve(self, request, *args, **kwargs):
        if not request.query_params or not request.query_params["sha"]:
            raise APIException("You must include 'sha' query parameter")

        sha = request.query_params["sha"]
        
        # We fetch by commitid and repo since there's an index on both of those
        commit = Commit.objects.get(commitid=sha, repository=self.repo)
        
        report_svc = ReportService()
        response = {}

        # Fetch critical paths so we know which files to focus on
        cpc_report = report_svc.build_critical_path_report_from_commit(commit)

        # Note on performance
        # I'm not sure in practice how many lines we can expect to be critical. Because
        # of that, and the fact that this is for demo purposes, I'm just going to iterate
        # through all critical paths until we find that it's not efficient.
        cpc_files = []
        for critical_file_path in cpc_report.keys():
            critical_lines = cpc_report[critical_file_path]
            
            # Gather all lines from this file
            lines = []
            for lineno in critical_lines:
                lines.append(CriticalPathLine(lineno))

            cpc_files.append(CriticalPathFile(critical_file_path, lines))
            
        # Serialize structure
        cpr = CriticalPathResponse(cpc_files)
        serializer = CriticalPathResponseSerializer(cpr)

        return Response(serializer.data)
