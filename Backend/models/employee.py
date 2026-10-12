from models.user import User


class Employee(User):
    ROLE = "employee"

    def __init__(self, *args, **kwargs):
        kwargs["role"] = self.ROLE
        super().__init__(*args, **kwargs)

