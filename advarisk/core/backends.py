from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Universal login backend:
    - Clients: email + password
    - Agents:  phone number OR email + password
    - Both:    username + password also works
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        user = None

        # 1. Try exact username match
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            pass

        # 2. Try email match
        if user is None:
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                pass

        # 3. Try phone number match (agents)
        if user is None:
            try:
                user = UserModel.objects.get(phone_number=username)
            except UserModel.DoesNotExist:
                pass

        if user is None:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
