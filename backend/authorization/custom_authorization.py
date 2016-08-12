"""Custom authorization functions."""
from __future__ import absolute_import
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized


class UserObjectsOnlyAuthorization(Authorization):
    """User object only authorization."""

    def update_list(self, object_list, bundle):
        """Update list users."""
        raise Unauthorized("Sorry, no update by bundle.")

    def update_detail(self, object_list, bundle):
        """Update user details."""
        return bundle.obj.user == bundle.request.user.userprofile or bundle.request.user.is_superuser

    def delete_detail(self, object_list, bundle):
        """Delete user detail."""
        return bundle.obj.user == bundle.request.user.userprofile or bundle.request.user.is_superuser

    def delete_list(self, object_list, bundle):
        """Delete list users."""
        raise Unauthorized("Sorry, no deletes by bundle")
