from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from django.test import TransactionTestCase
from freezegun import freeze_time

from codecov.commands.exceptions import ValidationError
from codecov_auth.models import Owner
from codecov_auth.tests.factories import OwnerFactory
from plan.constants import TRIAL_PLAN_SEATS, PlanName, TrialDaysAmount, TrialStatus

from ..start_trial import StartTrialInteractor


class StartTrialInteractorTest(TransactionTestCase):
    @async_to_sync
    def execute(self, current_user, org_username=None):
        current_user = current_user
        return StartTrialInteractor(current_user, "github").execute(
            org_username=org_username,
        )

    def test_start_trial_raises_exception_when_owner_is_not_in_db(self):
        current_user = OwnerFactory(
            username="random-user-123",
            service="github",
        )
        with pytest.raises(ValidationError):
            self.execute(current_user=current_user, org_username="some-other-username")

    @freeze_time("2022-01-01T00:00:00")
    def test_start_trial_raises_exception_when_owners_trial_status_is_ongoing(self):
        now = datetime.utcnow()
        trial_start_date = now
        trial_end_date = now + timedelta(days=3)
        current_user = OwnerFactory(
            username="random-user-123",
            service="github",
            trial_start_date=trial_start_date,
            trial_end_date=trial_end_date,
            trial_status=TrialStatus.ONGOING.value,
        )
        with pytest.raises(ValidationError):
            self.execute(current_user=current_user, org_username=current_user.username)

    @freeze_time("2022-01-01T00:00:00")
    def test_start_trial_raises_exception_when_owners_trial_status_is_expired(self):
        now = datetime.utcnow()
        trial_start_date = now + timedelta(days=-10)
        trial_end_date = now + timedelta(days=-4)
        current_user = OwnerFactory(
            username="random-user-123",
            service="github",
            trial_start_date=trial_start_date,
            trial_end_date=trial_end_date,
            trial_status=TrialStatus.EXPIRED.value,
        )
        with pytest.raises(ValidationError):
            self.execute(current_user=current_user, org_username=current_user.username)

    @freeze_time("2022-01-01T00:00:00")
    def test_start_trial_raises_exception_when_owners_trial_status_cannot_trial(
        self,
    ):
        now = datetime.utcnow()
        trial_start_date = now
        trial_end_date = now
        current_user = OwnerFactory(
            username="random-user-123",
            service="github",
            trial_start_date=trial_start_date,
            trial_end_date=trial_end_date,
            trial_status=TrialStatus.CANNOT_TRIAL.value,
        )
        with pytest.raises(ValidationError):
            self.execute(current_user=current_user, org_username=current_user.username)

    @freeze_time("2022-01-01T00:00:00")
    @patch("services.segment.SegmentService.trial_started")
    def test_start_trial_starts_trial_for_org_that_has_not_started_trial_before_and_calls_segment(
        self, trial_started_mock
    ):
        current_user: Owner = OwnerFactory(
            username="random-user-123",
            service="github",
            trial_start_date=None,
            trial_end_date=None,
            trial_status=TrialStatus.NOT_STARTED.value,
        )
        self.execute(current_user=current_user, org_username=current_user.username)
        current_user.refresh_from_db()

        now = datetime.utcnow()
        assert current_user.trial_start_date == now
        assert current_user.trial_end_date == now + timedelta(
            days=TrialDaysAmount.CODECOV_SENTRY.value
        )
        assert current_user.trial_status == TrialStatus.ONGOING.value
        assert current_user.plan == PlanName.TRIAL_PLAN_NAME.value
        assert current_user.plan_user_count == TRIAL_PLAN_SEATS
        assert current_user.plan_auto_activate == True

        trial_started_mock.assert_called_once_with(
            org_ownerid=current_user.ownerid,
            trial_details={
                "trial_plan_name": current_user.plan,
                "trial_start_date": now,
                "trial_end_date": now
                + timedelta(days=TrialDaysAmount.CODECOV_SENTRY.value),
            },
        )
