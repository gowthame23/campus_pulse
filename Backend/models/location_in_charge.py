from models.user import User


class LocationInCharge(User):
    ROLE = "location_in_charge"

    def __init__(self, *args, **kwargs):
        kwargs["role"] = self.ROLE
        super().__init__(*args, **kwargs)
