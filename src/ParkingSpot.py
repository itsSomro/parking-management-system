from datetime import datetime


class ParkingSpot:
    def __init__(self, spot_id, spot_type, spot_floor):
        self._spot_id = spot_id
        self._spot_type = spot_type
        self._spot_floor = spot_floor
        self._vehicle = None
        self._entry_time = None

    @property
    def vehicle(self):
        return self._vehicle

    @property
    def spot_floor(self):
        return self._spot_floor

    @property
    def spot_type(self):
        return self._spot_type.name

    @property
    def get_id(self):
        return self._spot_id

    @property
    def entry_time(self):
        return self._entry_time

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


    def park_vehicle(self, vehicle, historical_datetime=None):
        if self.is_free() and self.can_fit_vehicle(vehicle):
            self._vehicle = vehicle
            self._entry_time = historical_datetime if historical_datetime else datetime.now()
            return True
        else:
            return False


    def remove_vehicle(self):
        if not self.is_free():
            vehicle_to_return = self._vehicle
            start_time = self._entry_time

            self._vehicle = None
            self._entry_time = None

            return vehicle_to_return, start_time
        else:
            return None





