import logging
from rest_framework import status, renderers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.encoding import smart_text

from services.archive import ArchiveService

from .helpers import (
    parse_params
)

from upload.helpers import (
    determine_repo_for_upload,
    determine_upload_branch_to_use,
    determine_upload_pr_to_use,
    determine_upload_commit_to_use,
    insert_commit
)
from services.archive import get_minio_client
from services.segment import SegmentService
from utils.config import get_config

log = logging.getLogger(__name__)

class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        return smart_text(data, encoding=self.charset)

class UploadHandler(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [PlainTextRenderer]

    """
    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        response["Accept"] = "text/*"
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Method"] = "POST"
        response[
            "Access-Control-Allow-Headers"
        ] = "Origin, Content-Type, Accept, X-User-Agent"

        return response
    """

    def post(self, request, *args, **kwargs):
        # Parse request parameters
        request_params = {
            **self.request.query_params.dict(),  # query_params is a QueryDict, need to convert to dict to process it properly
            **self.kwargs,
        }
        
        upload_params = parse_params(request_params)

        repository = determine_repo_for_upload(upload_params)
        owner = repository.author

        log.info(
            "Found repository for upload request",
            extra=dict(
                upload_params=upload_params,
                repo_name=repository.name,
                owner_username=owner.username,
                commit=upload_params.get("commit"),
            ),
        )

        # Do some processing to handle special cases for branch, pr, and commit values, and determine which values to use
        # note that these values may be different from the values provided in the upload_params
        branch = determine_upload_branch_to_use(upload_params, repository.branch)
        pr = determine_upload_pr_to_use(upload_params)
        commitid = determine_upload_commit_to_use(upload_params, repository)

        # Save (or update, if it exists already) the commit in the database
        log.info(
            "Saving commit in database",
            extra=dict(
                commit=commitid,
                pr=pr,
                branch=branch,
                upload_params=upload_params,
            ),
        )
        insert_commit(
            commitid, branch, pr, repository, owner, upload_params.get("parent")
        )

        # we call minio directly here to minimize touchpoints with rest of codebase
        archive_service = ArchiveService(repository=repository)
        minio = get_minio_client()

        upload_url = minio.presigned_put_object("archive", "/".join(
            (
                "critical_path",
                f"{archive_service.storage_hash}",
                f"{commitid}.txt",
            )
        ))

        # send back a repsonse
        response.write(upload_url)

        request.META["HTTP_ACCEPT"] = "text/plain"

        response.status_code = status.HTTP_200_OK
        return response
