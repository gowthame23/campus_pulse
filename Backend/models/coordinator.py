from models.user import User


class Coordinator(User):
    ROLE = "coordinator"

    def __init__(self, *args, **kwargs):
        kwargs["role"] = self.ROLE
        super().__init__(*args, **kwargs)
