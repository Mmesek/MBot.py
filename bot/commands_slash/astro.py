from dataclasses import dataclass
from datetime import datetime
from math import atan2, cos, degrees, radians, sin, tan, tau

from dateutil import tz
from geopy import Location
from geopy.geocoders import Nominatim
from MFramework import Embed, Groups, register
from skyfield import almanac
from skyfield.api import (
    Angle,
    N,
    W,
    load,
    load_constellation_map,
    load_constellation_names,
    position_of_radec,
    wgs84,
)
from skyfield.framelib import ecliptic_frame
from skyfield.positionlib import Barycentric
from skyfield.vectorlib import VectorSum
from timezonefinder import TimezoneFinder

PLANETS = {
    10: "Sun",
    301: "Moon",
    1: "Mercury",
    2: "Venus",
    3: "Earth",
    4: "Mars",
    5: "Jupiter",
    6: "Saturn",
    7: "Uranus",
    8: "Neptune",
    9: "Pluto",
}

SIGNS = {
    "Aries": ((3, 21), (4, 19)),
    "Taurus": ((4, 20), (5, 20)),
    "Gemini": ((5, 21), (6, 20)),
    "Cancer": ((6, 21), (7, 22)),
    "Leo": ((7, 23), (8, 22)),
    "Virgo": ((8, 23), (9, 22)),
    "Libra": ((9, 23), (10, 22)),
    "Scorpio": ((10, 23), (11, 21)),
    "Sagittarius": ((11, 22), (12, 21)),
    "Capricorn": ((12, 22), (1, 19)),
    "Aquarius": ((1, 20), (2, 18)),
    "Pisces": ((2, 19), (3, 20)),
}
STATIC_SIGNS = list(SIGNS.keys())

MOON_PHASES = {
    "New Moon": (0, 20),
    "Waxing Crescent": (20, 90),
    "First Quarter": (89, 91),
    "Waxing Gibbous": (90, 180),
    "Full Moon": (179, 181),
    "Waning Gibbous": (180, 270),
    "Last Quarter": (269, 271),
    "Waning Crescent": (270, 360),
}

TS = load.timescale()
CONSTELLATIONS = dict(load_constellation_names())

constellation_at = load_constellation_map()
EPHEMERIS = load("data/de422.bsp")

TF = TimezoneFinder()
_LOCATOR = Nominatim(user_agent="app")


def get_sign(angle: float):
    return STATIC_SIGNS[int(angle // 30)]


@dataclass
class Position:
    planet: str
    ra_hours: float
    dec_degrees: float
    dis_au: float

    @property
    def sign(self):
        return get_sign(self.angle)

    def cusp_difference(self):
        """Normalizes difference to 0-2 range for differences below 2 degrees"""
        degree = (self.angle) % 30
        if degree >= 28:
            return 30 - degree
        else:
            return degree

    def cusp_strength(self):
        """
        Represents how close current sign is to another one between 0 and 1.
        Higher = closer. Below 0 means that nearest sign is further than 2 degrees away"""
        return 1 - self.cusp_difference() / 2

    @property
    def cusp(self):
        """Returns Current Sign, previous or next Sign, and Strength how close it is according to angle"""
        n = get_sign(self.angle + 2)
        p = get_sign(self.angle - 2)
        if n == p:
            return False

        if n == self.sign:
            current = n
            related = p
        else:
            current = p
            related = n
        return current, related, self.cusp_strength()

    @property
    def angle(self):
        return (self.ra_hours * 15) % 360

    @property
    def constellation(self):
        return CONSTELLATIONS[constellation_at(self.get_position_of_radec())].replace("Capricornus", "Capricorn")

    def get_position_of_radec(self):
        return position_of_radec(self.ra_hours, self.dec_degrees, self.dis_au)


def get_position(observer: Barycentric, planet: int | str) -> Position:
    # ra, dec, dis = planets[planet].at(observer.t).radec()  # For sidereal?
    # ra, dec, dis = observer.observe(planets[planet]).apparent()#.altaz() # For tropical?
    ra, dec, dis = observer.observe(EPHEMERIS[planet]).apparent().radec()
    return Position(PLANETS[planet], ra.hours, dec.degrees, dis.au)


def fetch_positions(observer: Barycentric) -> dict[str, Position]:
    return {planet: get_position(observer, x) for x, planet in PLANETS.items()}


def sun_sign(dt: datetime) -> str:
    """
    >>> sun_sign(datetime(1, 9, 24))  # Second day
    'Libra'
    >>> sun_sign(datetime(1, 12, 31))  # Last day of month
    'Capricorn'
    >>> sun_sign(datetime(1, 1, 1))  # First day of month
    'Capricorn'
    >>> sun_sign(datetime(1, 4, 19))  # Last Day
    'Aries'
    >>> sun_sign(datetime(1, 1, 20))  # First Day
    'Aquarius'
    """
    for sign, ranges in SIGNS.items():
        start, end = ranges
        start_month, start_day = start
        end_month, end_day = end
        if start_month == dt.month and start_day <= dt.day or dt.month == end_month and dt.day <= end_day:
            return sign


def check(observer: Barycentric, expected: dict[str, tuple[str, str]]):
    for planet, position in fetch_positions(observer).items():
        if planet in expected:
            if expected[planet][0] != position.sign:
                print(
                    f"[Sign             ] {planet}: {position.angle} {position.sign} != {expected[planet][0]}. Cusp: {position.cusp}, {position.cusp_strength()}"
                )
            if expected[planet][1] != position.constellation:
                print(
                    f"[Constellation  AS] {planet}: {position.angle} {position.constellation} != {expected[planet][1]}. Cusp: {position.cusp}, {position.cusp_strength()}"
                )
            if expected[planet][2] != position.constellation:
                print(
                    f"[Constellation MTZ] {planet}: {position.angle} {position.constellation} != {expected[planet][2]}. Cusp: {position.cusp}, {position.cusp_strength()}"
                )


def tropical_ascendant(observer: Barycentric, planet: str = "sun"):
    ra, dec, dis = observer.observe(EPHEMERIS[planet]).apparent().radec()
    r_sun, _, _ = EPHEMERIS[planet].at(observer.t).radec()
    asc = (ra.hours * 15 - r_sun._degrees) % 360
    return get_sign(asc)


def sidereal_mc(observer: Barycentric):
    asc = (observer.t.gast * 15) % 360
    return get_sign(asc)


def tropical_ascendant_math(dt: datetime, coordinates: Location):
    DAY_ZERO = datetime(2000, 1, 1, 12, tzinfo=tz.UTC)
    T = ((dt - DAY_ZERO).total_seconds() / 86400) / 36525

    oe = ((((-4.34e-8 * T - 5.76e-7) * T + 0.0020034) * T - 1.831e-4) * T - 46.836769) * T / 3600 + 23.4392794444444
    gmst = (67310.548 + (3155760000 + 8640184.812866) * T + 0.093104 * T**2 - 6.2e-6 * T**3) / 3600 % 24

    lstr = radians(((gmst + coordinates.longitude / 15) % 24) * 15)
    oer = radians(oe)
    ascr = atan2(cos(lstr), -(sin(lstr) * cos(oer) + tan(radians(coordinates.latitude)) * sin(oer)))

    asc = degrees(ascr) % 360
    return get_sign(asc)


class Chart:
    def __init__(
        self, city: str, year: int = 1, month: int = 1, day: int = 1, hour: int = 12, minute: int = 0, second: int = 0
    ) -> None:
        self.coordinates: Location = _LOCATOR.geocode(city)
        # print(self.coordinates.latitude, self.coordinates.longitude)
        self.dt = datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            tzinfo=tz.gettz(TF.timezone_at(lat=self.coordinates.latitude, lng=self.coordinates.longitude)),
        )
        location: VectorSum = EPHEMERIS["earth"] + wgs84.latlon(
            self.coordinates.latitude * N, self.coordinates.longitude * W
        )
        self.ts = TS.from_datetime(self.dt)
        self.observer: Barycentric = location.at(self.ts)

    def sidereal(self):
        return {
            **{k: v.constellation for k, v in fetch_positions(self.observer).items()},
            "Ascendant": None,
            "Mid-Haven": sidereal_mc(self.observer),
        }

    def tropical(self):
        return {
            **{k: v.sign for k, v in fetch_positions(self.observer).items()},
            "Ascendant": tropical_ascendant(self.observer),
        }

    def moon_phase(self) -> str:
        angle = almanac.moon_phase(EPHEMERIS, self.ts)
        for phase, (start, end) in MOON_PHASES.items():
            if start <= angle.degrees <= end:
                print(angle.degrees)
                return phase

    def season(self) -> str:
        s = almanac.seasons(EPHEMERIS)
        return ("Spring", "Summer", "Autumn", "Winter")[s(self.ts)]

    def localized_moon_phase(self):
        _, mlon, _ = self.observer.observe(EPHEMERIS["moon"]).apparent().frame_latlon(ecliptic_frame)
        _, slon, _ = self.observer.observe(EPHEMERIS["sun"]).apparent().frame_latlon(ecliptic_frame)
        return Angle(radians=(mlon.radians - slon.radians) % tau)


@register(group=Groups.GLOBAL, private_response=True)
async def zodiac(birth_date: str, city: str):
    """
    Calculate your zodiac signs. Outputs in both Sidereal & Tropical systems.
    Params
    ------
    birth_date:
        Birth date to calculate number from. Format: YYYY-MM-DD HH:MM
    city:
        City, Country of birthplace
    """
    if " " not in birth_date:
        date = birth_date
        hour = "12"
    else:
        date, hour = birth_date.split(" ", 1)
    y, m, d = [int(i) for i in date.split("-")]
    hour = hour.split(":")

    h, mm, s = 12, 0, 0
    match len(hour):
        case 1:
            h = int(hour[0])
        case 2:
            h, mm = [int(i) for i in hour]
        case _:
            h, mm, s = [int(i) for i in hour[:3]]

    chart = Chart(city, y, m, d, h, mm, s)
    return (
        Embed()
        .add_field("Sidereal", "".join(chart.sidereal()), True)
        .add_field(
            "Tropical",
            "".join({"Sun": sun_sign(chart.dt), "Ascendant": tropical_ascendant_math(chart.dt, chart.coordinates)}),
            True,
        )
    )
