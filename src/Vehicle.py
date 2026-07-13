from abc import ABC, abstractmethod
from enum import Enum


class VehicleSize(Enum):
    SCOOTER = 'S'
    CAR = 'C'
    TRUCK = 'T'

class Vehicle(ABC):
    def __init__(self, license_plate):
        self._license_plate = license_plate

    @property
    def license_plate(self):
        return self._license_plate

    @abstractmethod
    def get_type(self):
        pass

class Scooter(Vehicle):
    def get_type(self):
        return VehicleSize.SCOOTER

class Car(Vehicle):
    def get_type(self):
        return VehicleSize.CAR

class Truck(Vehicle):
    def get_type(self):
        return VehicleSize.TRUCK

