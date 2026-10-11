from models.user import User


class Student(User):
    ROLE = "student"

    def __init__(self, *args, **kwargs):
        kwargs["role"] = self.ROLE
        super().__init__(*args, **kwargs)
