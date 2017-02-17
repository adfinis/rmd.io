from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


class EmailBackend(object):
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)

            if user.is_active and user.check_password(password):
                return user
            else:
                return None

        except UserModel.DoesNotExist:
            return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
