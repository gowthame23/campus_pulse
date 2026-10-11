from models.user import User


class AppManager(User):
    ROLE = "app_manager"

    def __init__(self, *args, **kwargs):
        kwargs["role"] = self.ROLE
        super().__init__(*args, **kwargs)
