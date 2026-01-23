class ParkingSpot:
    def __init__(self, spot_id, spot_type):
        self._spot_id = spot_id
        self._spot_type = spot_type
        self._vehicle = None

    @property
    def vehicle(self):
        return self._vehicle

    @property
    def spot_type(self):
        return self._spot_type.name

    @property
    def get_id(self):
        return self._spot_id


    def is_free(self):
        if self._vehicle is None:
            return True
        else:
            return False


    def can_fit_vehicle(self, vehicle):
        v_type = vehicle.get_type()
        if self._spot_type == v_type:
            return True
        else:
            return False


    def park_vehicle(self, vehicle):
        if self.is_free() and self.can_fit_vehicle(vehicle):
            self._vehicle = vehicle
            return True
        else:
            return False


    def remove_vehicle(self):
        if not self.is_free():
            vehicle_to_return = self._vehicle
            self._vehicle = None
            return vehicle_to_return
        else:
            return None





