from models.user import User


class Administrator(User):
    ROLE = "administrator"

    def __init__(self, *args, **kwargs):
        kwargs["role"] = self.ROLE
        super().__init__(*args, **kwargs)
