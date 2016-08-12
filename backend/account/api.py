"""All account apis will be defined here."""

from __future__ import absolute_import
from django.contrib.auth import authenticate, login, logout
from django.conf.urls import url
from django.db import transaction
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie.http import HttpUnauthorized
from tastypie.utils import trailing_slash
from tastypie.models import ApiKey
from tastypie import fields
from .signals import * # noqa
from .authentication import ApiKeyAuthenticationExt
from .validation import UserProfileValidation
from ..commons.custom_exception import CustomBadRequest
from ..commons.multipart_resource import MultipartResource
import os


class InternalUserResource(ModelResource):
    """Internal user resource class."""

    class Meta(object):
        """Internal user resource meta data."""

        queryset = User.objects.all() # noqa
        excludes = ['password', 'is_superuser']
        resource_name = 'auth/users'
        authenticate = ApiKeyAuthenticationExt()
        authorization = Authorization()


class UserResource(ModelResource):
    """User model resources."""

    class Meta(object):
        """User model resource meta data."""

        queryset = User.objects.all() # noqa
        fields = ['username', 'first_name', 'last_name']
        excludes = ['email', 'password', 'is_superuser']
        resource_name = 'auth/users'
        authentication = ApiKeyAuthenticationExt()
        authorization = Authorization()


class UserImageResource(ModelResource):
    """User image model resource."""

    original = fields.CharField(attribute='get_original_url')
    medium = fields.CharField(attribute='get_medium_url')
    small = fields.CharField(attribute='get_small_url')

    class Meta(object):
        """User image resource meta data."""

        queryset = UserImage.objects.all() # noqa
        fields = ['id', 'original']
        resource_name = 'userimage'
        authorization = Authorization()
        authentication = ApiKeyAuthenticationExt()
        always_return_data = True


class InternalUserProfileResource(ModelResource):
    """Internal user profile resource models."""

    image = fields.ForeignKey(UserImageResource, 'image', full=True, null=True, readonly=True)
    first_name = fields.CharField(attribute='user__first_name', null=True)
    last_name = fields.CharField(attribute='user__last_name', null=True)

    class Meta(object):
        """Internal user profile resource meta data."""

        queryset = UserProfile.objects.all().prefetch_related('user') # noqa
        fields = ['id']
        resource_name = 'auth/user'
        authentication = ApiKeyAuthenticationExt()
        authorization = Authorization()
        filtering = {
            "id": 'exact'
        }


class UserProfileResource(MultipartResource, ModelResource):
    """User profile resource models."""

    user = fields.ToOneField(InternalUserResource, attribute='user', null=True)
    image = fields.ForeignKey(UserImageResource, 'image', full=True, null=True)
    first_name = fields.CharField(attribute='user__first_name', null=True)
    last_name = fields.CharField(attribute='user__last_name', null=True)
    email = fields.CharField(attribute='user__email', null=True)

    class Meta(object):
        """Meta data."""

        queryset = UserProfile.objects.prefetch_related('user').prefetch_related('image') # noqa
        resource_name = 'userprofile'
        always_return_data = True
        authentication = ApiKeyAuthenticationExt()
        authorization = Authorization()
        validation = UserProfileValidation()

    def hydrate(self, bundle):
        """Tastypie hydrate method."""
        bundle.data['user'] = {}
        profile = UserProfile.objects.filter(user__id=bundle.request.user.id).first() # noqa
        userprofile = User.objects.filter(id=bundle.request.user.id).first() # noqa
        bundle.data['user'] = {
            'id': bundle.request.user.id,
            'first_name': userprofile.first_name,
            'last_name': userprofile.last_name,
            'email': userprofile}
        if profile.image:
            api_uri = os.path.split(os.path.split(self.get_resource_uri())[0])[0]
            resource_uri = '/'.join((api_uri, UserImageResource.Meta.resource_name, str(profile.image.id), ''))
            bundle.data['user']['image'] = {'id': profile.image.id,
                                            'resource_uri': resource_uri,
                                            'original': profile.image.get_original_url(),
                                            "medium": profile.image.get_medium_url(),
                                            "small": profile.image.get_small_url()}

        return super(UserProfileResource, self).hydrate(bundle)

    def prepend_urls(self):
        """Urls."""
        return [
            url(r"^(?P<resource_name>%s)/profile-image%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('upload_profile_image'), name="api_upload_profile_image"),
        ]

    def upload_profile_image(self, request, **kwargs):
        """Upload profile image handler method."""
        self.is_authenticated(request)
        self.method_check(request, allowed=['post'])
        self.throttle_check(request)

        # Create new image
        userimage = UserImage(original=request.FILES['original']) # noqa
        userimage.save()

        # Tie image to user profile
        updated = UserProfile.objects.filter(user__id=request.user.id).update(image=userimage) # noqa

        api_uri = os.path.split(os.path.split(self.get_resource_uri())[0])[0]

        resource_uri = '/'.join((api_uri, UserImageResource.Meta.resource_name, str(userimage.id), ''))

        self.log_throttled_access(request)
        return self.create_upload_response(request, resource_uri, userimage, updated)

    def create_upload_response(self, request, resource_uri, image_model, success):
        """Return uploaded image response."""
        if success:
            return self.create_response(request, {"success": True,
                                                  "resource_uri": resource_uri,
                                                  "original": image_model.get_original_url(),
                                                  "medium": image_model.get_medium_url(),
                                                  "small": image_model.get_small_url()})
        else:
            raise CustomBadRequest(error_type='UNKNOWNERROR', error_message="Can't update user profile image")


class AuthenticationResource(ModelResource):
    """Authentication resource."""

    class Meta(object):
        """Meta data."""

        allowed_methods = ['get', 'post']
        always_return_data = True
        authentication = Authentication()
        authorization = Authorization()
        queryset = User.objects.all() # noqa
        resource_name = 'authentication'
        fields = ['username', 'email', 'password', 'image']

    def prepend_urls(self):
        """Api urls."""
        return [
            url(r"^(?P<resource_name>%s)/sign_in%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_in'), name="api_sign_in"),
            url(r"^(?P<resource_name>%s)/sign_up%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_up_by_email'), name="api_sign_up_by_email"),
            url(r"^(?P<resource_name>%s)/sign_out%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_out'), name="api_sign_out"),
        ]

    def sign_in(self, request, **kwargs):
        """Sign in api handler."""
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/join'))
        retype_password = data.get('retype_password', None)
        if retype_password is not None:
            return self.sign_up_by_email(request, **kwargs)
        elif 'email' in data and 'password' in data:
            return self.sign_in_by_email(request, **kwargs)
        else:
            raise CustomBadRequest(error_type='UNAUTHORIZED')

    def sign_in_by_email(self, request, **kwargs):
        """Sign in by email api handler."""
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/join'))

        email = data.get('email', '')
        password = data.get('password', '')
        user = User.objects.filter(email=email).first() # noqa

        if user:
            if user.check_password(password):
                user = authenticate(username=email, password=password)
                login(request, user)
                apikey = ApiKey.objects.filter(user=user).first()
                return self.create_auth_response(request=request, user=user, api_key=apikey.key, is_new=True)
            else:
                raise CustomBadRequest(error_type='UNAUTHORIZED', error_message='Your password is not correct')
        else:
            raise CustomBadRequest(error_type='UNAUTHORIZED',
                                   error_message='Your email address is not registered. Please register')

    def sign_up_by_email(self, request, **kwargs):
        """Sign up by email handler."""
        self.method_check(request, allowed=['post'])
        # data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/join'))
        data = request.POST

        email = data.get('email', '')
        password = data.get('password', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if last_name:
            last_name = last_name.strip()
        if first_name:
            first_name = first_name.strip()

        if User.objects.filter(email__iexact=email).exists(): # noqa
            raise CustomBadRequest(error_type='DUPLICATE_VALUE', field='email', obj='email')
        else:
            try:
                with transaction.atomic():

                    User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name) # noqa
                    user = authenticate(username=email, password=password)

                    login(request, user)

                    if user is not None:
                        self.create_userprofile(user.id)
                        apikey = ApiKey.objects.filter(user=user).first()
                        self.upload_user_image(request, **kwargs)
                        return self.create_auth_response(request=request, user=user, api_key=apikey.key, is_new=True)
                    else:
                        raise CustomBadRequest(error_type='UNKNOWN_ERROR', error_message='Cant sign up by this email.')
            except ValueError as e:
                raise CustomBadRequest(error_type='UNKNOWN_ERROR', error_message=str(e))

    def upload_user_image(self, request, **kwargs):
        """Upload user image handler."""
        if 'original' in request.FILES:
            userimage = UserImage(original=request.FILES['original']) # noqa
            if userimage:
                userimage.save()
                # Tie image to user profile
                UserProfile.objects.filter(user__id=request.user.id).update(image=userimage) # noqa

    def sign_out(self, request, **kwargs):
        """Sign out handler."""
        self.is_authenticated(request)
        self.method_check(request, allowed=['post', 'get'])

        if request.user and request.user.is_authenticated():
            logout(request)

            return self.create_response(request, {'success': True})
        else:
            return self.create_response(request, {'success': False}, HttpUnauthorized)

    def create_auth_response(self, request, user, api_key, is_new=False):
        """Genetate response data for authentication process."""
        userprofile = UserProfile.objects.get(id=user.userprofile.id) # noqa

        resource_instance = UserProfileResource()
        bundle = resource_instance.full_hydrate(resource_instance.build_bundle(obj=userprofile, request=request))
        bundle.data['user']['api_key'] = api_key
        bundle.data['user']['is_new'] = is_new

        return self.create_response(request, bundle)

    def create_userprofile(self, user_id, **kwargs):
        """Create blank user profile base on user_id."""
        # Add the user_id to kwargs
        kwargs['user_id'] = user_id

        # register_type = kwargs.get('register_type', None)
        # is_facebook = register_type == 1

        # Create user profile
        userprofile, _ = UserProfile.objects.get_or_create(user__id=user_id, defaults=kwargs) # noqa

        if userprofile is None:
            raise CustomBadRequest(error_type='UNKNOWNERROR', error_message="Can't create userprofile and address")
