#
#   Position Coordinate Conversions
#
import datetime
from math import atan2, sqrt, sin, cos, pi, degrees


# WGS84 constants
WGS84_EARTH_a = 6378137.0
WGS84_EARTH_b = 6356752.31424518
WGS84_EARTH_a2_b2 = (WGS84_EARTH_a * WGS84_EARTH_a - WGS84_EARTH_b * WGS84_EARTH_b)
WGS84_EARTH_e2 = WGS84_EARTH_a2_b2 / (WGS84_EARTH_a * WGS84_EARTH_a)
WGS84_EARTH_ee2 = WGS84_EARTH_a2_b2 / (WGS84_EARTH_b * WGS84_EARTH_b)

def ecef_to_wgs84(ecef_x_m, ecef_y_m, ecef_z_m):
    """ 
    Convert ECEF coordinates (m) to lat/lon/alt in a WGS84 datum 
    Ported from ecef2elli from rs41mod.c
    """

    lam = atan2( ecef_y_m, ecef_x_m )

    p = sqrt( ecef_x_m * ecef_x_m + ecef_y_m * ecef_y_m)
    t = atan2( ecef_z_m * WGS84_EARTH_a , p * WGS84_EARTH_b)

    phi = atan2( 
        ecef_z_m + WGS84_EARTH_ee2 * WGS84_EARTH_b * sin(t)*sin(t)*sin(t),
        p - WGS84_EARTH_e2 * WGS84_EARTH_a * cos(t)*cos(t)*cos(t)
    )

    R = WGS84_EARTH_a / sqrt( 1 - WGS84_EARTH_e2*sin(phi)*sin(phi))

    alt = p / cos(phi) - R
    lat = phi * 180/pi
    lon = lam * 180/pi

    return (lat, lon, alt)


def ecef_velocity(lat, lon, ecef_vel_x, ecef_vel_y, ecef_vel_z):
    """
    Convert ECEF Velocities (m/s) to Horizontal / Vertical speeds, and direction of travel.
    Requires lat/lon (processed using ecef_to_wgs84) as an input.
    """

    phi = lat * pi/180.0
    lam = lon * pi/180.0

    # Calculate out N/S, E/W, U/D speed vectors
    vN = -1.0*ecef_vel_x*sin(phi)*cos(lam)  - ecef_vel_y*sin(phi)*sin(lam) + ecef_vel_z*cos(phi)
    vE = -1.0*ecef_vel_x*sin(lam)           + ecef_vel_y*cos(lam)
    vU = ecef_vel_x*cos(phi)*cos(lam)       + ecef_vel_y*cos(phi)*sin(lam) + ecef_vel_z*sin(phi)

    # Ground speed and Ascent Rate
    ground_speed = sqrt(vN*vN + vE*vE)
    ascent_rate = vU

    # Traditional U/V wind vector components
    wind_u = vE
    wind_v = vN

    # Heading of travel
    heading = degrees(atan2(vE, vN))
    if heading < 0:
        heading += 360.0

    return (ground_speed, ascent_rate, wind_u, wind_v, heading)


def gps_weeksecondstoutc(gpsweek, gpsseconds, leapseconds=0):
    """ Convert time in GPS time (GPS Week, seconds-of-week) to a UTC timestamp """
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00","%Y-%m-%d %H:%M:%S")
    elapsed = datetime.timedelta(days=(gpsweek*7),seconds=(gpsseconds))
    timestamp = epoch + elapsed - datetime.timedelta(seconds=leapseconds)
    return timestamp


if __name__ == "__main__":

    LATLON_TOLERANCE = 0.000005
    ALT_TOLERANCE = 0.1

    tests = [
        [-3920900.06, 3466390.67, -3633506.63, -34.95202, 138.52073, 3.0]
    ]

    for test in tests:
        (lat, lon, alt) = ecef_to_wgs84(test[0], test[1], test[2])

        _test_results = f"In: ({test[0]}, {test[1]}, {test[2]})  Out: ({lat}, {lon}, {alt}), Expected: ({test[3]}, {test[4]}, {test[5]})  - "

        if (abs(lat - test[3]) < LATLON_TOLERANCE) and ((abs(lon - test[4]) < LATLON_TOLERANCE)) and (abs(alt-test[5]) < ALT_TOLERANCE):
            _test_results += "PASS"
        else:
            _test_results += "FAIL"
        
        print(_test_results)
