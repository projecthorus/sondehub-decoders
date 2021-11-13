#
#   Position Coordinate Conversions
#
from math import atan2, sqrt, sin, cos, pi

# from rs41mod.c
#
# // WGS84/GRS80 Ellipsoid
# #define EARTH_a  6378137.0
# #define EARTH_b  6356752.31424518
# #define EARTH_a2_b2  (EARTH_a*EARTH_a - EARTH_b*EARTH_b)

# const
# double a = EARTH_a,
#        b = EARTH_b,
#        a_b = EARTH_a2_b2,
#        e2  = EARTH_a2_b2 / (EARTH_a*EARTH_a),
#        ee2 = EARTH_a2_b2 / (EARTH_b*EARTH_b);

# static void ecef2elli(double X[], double *lat, double *lon, double *alt) {
#     double phi, lam, R, p, t;

#     lam = atan2( X[1] , X[0] );

#     p = sqrt( X[0]*X[0] + X[1]*X[1] );
#     t = atan2( X[2]*a , p*b );

#     phi = atan2( X[2] + ee2 * b * sin(t)*sin(t)*sin(t) ,
#                  p - e2 * a * cos(t)*cos(t)*cos(t) );

#     R = a / sqrt( 1 - e2*sin(phi)*sin(phi) );
#     *alt = p / cos(phi) - R;

#     *lat = phi*180/M_PI;
#     *lon = lam*180/M_PI;
# }

# WGS84 constants
WGS84_EARTH_a = 6378137.0
WGS84_EARTH_b = 6356752.31424518
WGS84_EARTH_a2_b2 = (WGS84_EARTH_a * WGS84_EARTH_a - WGS84_EARTH_b * WGS84_EARTH_b)
WGS84_EARTH_e2 = WGS84_EARTH_a2_b2 / (WGS84_EARTH_a * WGS84_EARTH_a)
WGS84_EARTH_ee2 = WGS84_EARTH_a2_b2 / (WGS84_EARTH_b * WGS84_EARTH_b)

def ecef_to_wgs84(ecef_x_m, ecef_y_m, ecef_z_m):
    """ 
    Convert ECEF coordinates to lat/lon/alt in a WGS84 datum 
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


def ecef_velocity(lat, lon, ecef_v_x, ecef_v_y, ecef_v_z):
    """
    Convert ECEF Velocities to Horizontal / Vertical speeds, and direction of travel.
    Requires lat/lon (processed using ecef_to_wgs84) as an input.
    """

    

    return (vel_h, vel_v, heading)

    # // ECEF-Velocities
    # // ECEF-Vel -> NorthEastUp
    # phi = lat*M_PI/180.0;
    # lam = lon*M_PI/180.0;
    # vN = -V[0]*sin(phi)*cos(lam) - V[1]*sin(phi)*sin(lam) + V[2]*cos(phi);
    # vE = -V[0]*sin(lam) + V[1]*cos(lam);
    # vU =  V[0]*cos(phi)*cos(lam) + V[1]*cos(phi)*sin(lam) + V[2]*sin(phi);

    # // NEU -> HorDirVer
    # gpx->vH = sqrt(vN*vN+vE*vE);   // HORIZONTAL SPEED

    # dir = atan2(vE, vN) * 180 / M_PI;
    # if (dir < 0) dir += 360;
    # gpx->vD = dir;  // HEADING

    # gpx->vV = vU; // ASCENT RATE



if __name__ == "__main__":

    tests = [
        [2792680.28, 1357809.67, 5552663.50]
    ]

    for test in tests:
        (lat, lon, alt) = ecef_to_wgs84(test[0], test[1], test[2])

        print(f"In: ({test[0]}, {test[1]}, {test[2]})  Out: ({lat}, {lon}, {alt})")