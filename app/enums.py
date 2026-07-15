from enum import Enum


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class ClubEnum(str, Enum):
    LEFT = "Left"
    RIGHT = "Right"
    CENTER = "Center"
    