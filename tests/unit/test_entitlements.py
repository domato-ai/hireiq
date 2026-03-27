"""
Unit tests for plan entitlement checks.

Entitlement logic lives in apps/api/app/entitlements/.
Run with:
    pytest tests/unit/test_entitlements.py -v
"""

import pytest

# ---------------------
# TODO: Import once entitlement module is implemented.
# from app.entitlements.checker import can_upload, can_score, get_limits
# from app.entitlements.models import Plan
# ---------------------


class TestUploadEntitlements:
    """Tests for upload / document limits per plan."""

    def test_placeholder_passes(self):
        """Placeholder — replace with real assertions."""
        assert True

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_free_plan_upload_limit(self):
        """Free plan should allow at most 10 uploads per month."""
        # limits = get_limits(Plan.free)
        # assert limits.uploads_per_month == 10
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_pro_plan_upload_limit(self):
        """Pro plan should allow at most 200 uploads per month."""
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_team_plan_upload_limit(self):
        """Team plan should have unlimited uploads (None)."""
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_can_upload_returns_false_when_limit_reached(self):
        """can_upload should return False when monthly quota is exhausted."""
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_can_upload_returns_true_when_under_limit(self):
        """can_upload should return True when usage is below quota."""
        pass


class TestScoringEntitlements:
    """Tests for scoring / AI call limits per plan."""

    def test_placeholder_passes(self):
        assert True

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_free_plan_scoring_limit(self):
        """Free plan should allow at most 5 AI scoring runs per month."""
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_can_score_returns_false_when_limit_reached(self):
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_expired_subscription_falls_back_to_free_limits(self):
        """A lapsed Pro subscription should revert to free-tier limits."""
        pass


class TestWorkspaceEntitlements:
    """Tests for workspace / seat limits."""

    def test_placeholder_passes(self):
        assert True

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_free_plan_single_workspace(self):
        """Free plan should allow only 1 workspace."""
        pass

    @pytest.mark.skip(reason="Entitlement module not yet implemented")
    def test_team_plan_multiple_workspaces(self):
        """Team plan should allow unlimited workspaces."""
        pass
