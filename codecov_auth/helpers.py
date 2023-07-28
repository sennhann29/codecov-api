import traceback

import requests
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from codecov_auth.constants import GITLAB_BASE_URL

GITLAB_PAYLOAD_AVATAR_URL_KEY = "avatar_url"


def get_gitlab_url(email, size):
    res = requests.get(
        "{}/api/v4/avatar?email={}&size={}".format(GITLAB_BASE_URL, email, size)
    )
    url = ""
    if res.status_code == 200:
        data = res.json()
        try:
            url = data[GITLAB_PAYLOAD_AVATAR_URL_KEY]
        except KeyError:
            pass

    return url


def current_user_part_of_org(owner, org):
    if owner is None:
        return False
    if owner == org:
        return True
    # owner is a direct member of the org
    orgs_of_user = owner.organizations or []
    return org.ownerid in orgs_of_user


# https://stackoverflow.com/questions/7905106/adding-a-log-entry-for-an-action-by-a-user-in-a-django-ap
add = ADDITION
change = CHANGE
delete = DELETION


class History:
    @staticmethod
    def log(objects, message, action_flag=None, user=None, add_traceback=False):
        User = get_user_model()
        if user is None:
            user = User.objects.get()

        if action_flag is None:
            action_flag = change

        if type(objects) is not list:
            objects = [objects]

        if add_traceback:
            message = f"{message}: {traceback.format_stack()}"

        for o in objects:
            if not o:
                continue

            LogEntry.objects.log_action(
                user_id=user.pk,
                content_type_id=ContentType.objects.get_for_model(o).pk,
                object_repr=str(o),
                object_id=o.ownerid,
                change_message=message,
                action_flag=action_flag,
            )
