#!/usr/bin/env python
# -*- coding: utf8 -*-
# Import DroneKit-Python
from dronekit import VehicleMode, LocationGlobalRelative, LocationGlobal, Command, connect
import time
import math
from pymavlink import mavutil
def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the
    specified `original_location`. The returned Location has the same `alt` value
    as `original_location`.

    The function is useful when you want to move the vehicle around specifying locations relative to
    the current vehicle position.
    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
    For more information see:
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """
    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

    # New position in decimal degrees
    newlat = original_location.lat + (dLat * 180 / math.pi)
    newlon = original_location.lon + (dLon * 180 / math.pi)
    return LocationGlobal(newlat, newlon, original_location.alt)
def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5
def status_printer(txt):
    print('status urpylka')
    print(txt)
class autocopterDronekit(object):
    def __init__(self):
        self.vehicle = None
        # Connect to the Vehicle (in this case a UDP endpoint)
        #проверка на подключается или нет
        #цикл пока не подключится?
        #http://python.dronekit.io/automodule.html#dronekit.connect
        self.vehicle = connect('tcp:127.0.0.1:14600', wait_ready=True,status_printer=status_printer)
        self.stop_takeoff = False
        self.stop_land = False
    def status(self):
        return self.status
    def status_of_connect(self):
        return True
    def disconnect(self):
        '''
        Close vehicle object before exiting script
        :return:
        '''
        if self.vehicle != None:
            self.vehicle.close()
    def get_status(self):
        # Get some vehicle attributes (state)
        buf = "Get some vehicle attribute values:" + \
              "\nGPS: %s" % self.vehicle.gps_0 + \
              "\nBattery: %s" % self.vehicle.battery + \
              "\nLast Heartbeat: %s" % self.vehicle.last_heartbeat + \
              "\nIs Armable?: %s" % self.is_armable + \
              "\nSystem status: %s" % self.vehicle.system_status.state + \
              "\nMode: %s" % self.vehicle.mode.name + \
              "\nGlobal Location: %s" % self.vehicle.location.global_frame + \
              "\nLocal Location: %s" % self.vehicle.location.local_frame + \
              "\nAttitude: %s" % self.vehicle.attitude + \
              "\nHeading: %s" % self.vehicle.heading + \
              "\nGroundspeed: %s" % self.vehicle.groundspeed + \
              "\nAirspeed: %s" % self.vehicle.airspeed
        return buf
    def onLand(self):
        return False
    def distance_to_current_waypoint(self):
        """
        Gets distance in metres to the current waypoint.
        It returns None for the first waypoint (Home location).
        """
        nextwaypoint = self.vehicle.commands.next
        if nextwaypoint == 0:
            return None
        missionitem = self.vehicle.commands[nextwaypoint - 1]  # commands are zero indexed
        lat = missionitem.x
        lon = missionitem.y
        alt = missionitem.z
        targetWaypointLocation = LocationGlobalRelative(lat, lon, alt)
        distancetopoint = get_distance_metres(self.vehicle.location.global_frame, targetWaypointLocation)
        return distancetopoint
    def download_mission(self):
        """
        Download the current mission from the vehicle.
        """
        cmds = self.vehicle.commands
        cmds.download()
        cmds.wait_ready()  # wait until download is complete.
    def adds_square_mission(self, aLocation, aSize):
        """
        Adds a takeoff command and four waypoint commands to the current mission.
        The waypoints are positioned to form a square of side length 2*aSize around the specified LocationGlobal (aLocation).

        The function assumes vehicle.commands matches the vehicle mission state
        (you must have called download at least once in the session and after clearing the mission)
        """
        cmds = self.vehicle.commands
        print " Clear any existing commands"
        cmds.clear()
        print " Define/add new commands."
        # Add new commands. The meaning/order of the parameters is documented in the Command class.

        # Add MAV_CMD_NAV_TAKEOFF command. This is ignored if the vehicle is already in the air.
        cmds.add(
            Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0,
                    0, 0, 0, 0, 10))
        # Define the four MAV_CMD_NAV_WAYPOINT locations and add the commands
        point1 = get_location_metres(aLocation, aSize, -aSize)
        point2 = get_location_metres(aLocation, aSize, aSize)
        point3 = get_location_metres(aLocation, -aSize, aSize)
        point4 = get_location_metres(aLocation, -aSize, -aSize)
        cmds.add(
            Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0,
                    0, 0, 0, point1.lat, point1.lon, 11))
        cmds.add(
            Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0,
                    0, 0, 0, point2.lat, point2.lon, 12))
        cmds.add(
            Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0,
                    0, 0, 0, point3.lat, point3.lon, 13))
        cmds.add(
            Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0,
                    0, 0, 0, point4.lat, point4.lon, 14))
        # add dummy waypoint "5" at point 4 (lets us know when have reached destination)
        cmds.add(
            Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0,
                    0, 0, 0, point4.lat, point4.lon, 14))
        print " Upload new commands to vehicle"
        cmds.upload()
    def switch_to_LAND(self, log_and_messages):
        self.stop_land = False
        self.vehicle.mode = VehicleMode("LAND")
        log_and_messages.deb_pr_tel('MODE = LAND')
        while not self.vehicle.system_status.state != 'STANBY':
            if not self.stop_land:
                log_and_messages.deb_pr_tel('Waiting for LAND')
                time.sleep(1)
            else:
                log_and_messages.deb_pr_tel('КРИТИЧЕСКОЕ ЗАВЕРШЕНИЕ! Stopped LAND!!! SWITCH TO IDLE')
                return 'IDLE'
        log_and_messages.deb_pr_tel('SUCCESS LAND! SWITCH TO IDLE')
        return 'IDLE'
        self.vehicle.armed = False
        log_and_messages.deb_pr_tel('Disarming...')
        log_and_messages.deb_pr_tel('IDLE STATE activated!')
    def switch_to_IDLE(self,log_and_messages):
        log_and_messages.deb_pr_tel('Switch to IDLE STATE')
        self.vehicle.mode = VehicleMode("GUIDED")
        log_and_messages.deb_pr_tel('MODE = GUIDED')
        self.vehicle.armed = False
        log_and_messages.deb_pr_tel('Disarming...')
        log_and_messages.deb_pr_tel('IDLE STATE activated!')
    def switch_to_GUIDED(self,log_and_messages):
        log_and_messages.deb_pr_tel('Go to GUIDED STATE.')
        self.vehicle.mode = VehicleMode("GUIDED")
        log_and_messages.deb_pr_tel('GUIDED STATE: MODE = GUIDED')
    def switch_to_RTL(self,log_and_messages):
        log_and_messages.deb_pr_tel('Go to RTL STATE.')
        self.vehicle.mode = VehicleMode("RTL")
        log_and_messages.deb_pr_tel('RTL STATE: MODE = RTL')
    @property
    def is_armable(self):
        """
        Returns `True` if the vehicle is ready to arm, false otherwise (``Boolean``).

        This attribute wraps a number of pre-arm checks, ensuring that the vehicle has booted,
        has a good GPS fix, and that the EKF pre-arm is complete.
        """
        # check that mode is not INITIALSING
        # check that we have a GPS fix
        # check that EKF pre-arm is complete
        return self.vehicle.mode != 'INITIALISING' and self.vehicle.gps_0.fix_type > 1# and self.vehicle._ekf_predposhorizabs #отключена проверка ekf
    def simple_goto_wrapper(self,lat,lot,alt=20,groundspeed=7.5):
        # Задаем координаты нужной точки
        a_location = LocationGlobalRelative(lat,lot,alt)
        # полетели
        self.vehicle.simple_goto(a_location)
        # Путевая скорость, м/с
        self.vehicle.groundspeed = groundspeed
    def arm_and_takeoff(self, aTargetAltitude,log_and_messages):
        """
        Arms vehicle and fly to aTargetAltitude.
        """
        self.stop_takeoff = False
        log_and_messages.deb_pr_tel('Basic pre-arm checks')
        # Don't let the user try to arm until autopilot is ready
        while not self.is_armable: #проверка не дронкита, а собственная
            if not self.stop_takeoff:
                log_and_messages.deb_pr_tel('Waiting for vehicle to initialise...')
                time.sleep(1)
            else:
                log_and_messages.deb_pr_tel('Stopping takeoff on pre-arm!')
                self.motors_off()
                return 'IDLE'
        # Copter should arm in GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")

        log_and_messages.deb_pr_tel('Arming motors')
        self.vehicle.armed = True

        while not self.vehicle.armed:
            if not self.stop_takeoff:
                log_and_messages.deb_pr_tel('Waiting for arming...')
                time.sleep(1)
            else:
                log_and_messages.deb_pr_tel('Stopping takeoff on arm!')
                self.motors_off()
                return 'IDLE'
        log_and_messages.deb_pr_tel('Taking off!')
        self.vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        while True:
            if not self.stop_takeoff:
                log_and_messages.deb_pr_tel("Altitude: %s" % self.vehicle.location.global_relative_frame.alt)
                if self.vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:  # Trigger just below target alt.
                    log_and_messages.deb_pr_tel("Reached target altitude")
                    break
                time.sleep(1)
            else:
                self.vehicle.armed = False
                log_and_messages.deb_pr_tel('Stopping takeoff on fly!')
                self.motors_off()
                #self.vehicle.attitude
                return 'IDLE'
        return 'GUIDED'

    def motors_off(self):
        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,  # target system, target component
            mavutil.mavlink.MAV_CMD_DO_FLIGHTTERMINATION,  # command
            0,  # confirmation
            1,  # Flight termination activated if > 0.5
            0, 0, 0, 0, 0, 0)
        self.vehicle.send_mavlink(msg)