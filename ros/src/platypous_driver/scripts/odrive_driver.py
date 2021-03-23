#!/usr/bin/env python3

import odrive
from odrive.enums import *

import time
import sys

class ODriveDriver:
    
    odrv       = None
    left_axis  = None
    right_axis = None
    
    brake_resistance = 5
    max_regen_current = 10
    dc_max_negative_current = -10
    
    motor_resistance_calib_max_voltage = 3
    motor_calibration_current = 5
    motor_pole_pairs = 5
    motor_type = MOTOR_TYPE_HIGH_CURRENT
    motor_current_lim = 7.0
    motor_current_control_bandwidth = 10
    
    encoder_cpr = 2048
    encoder_mode = ENCODER_MODE_INCREMENTAL
    
    controller_vel_limit = 10
    controller_vel_gain = 0.5
    controller_vel_integrator_gain = 0
    controller_control_mode = CONTROL_MODE_VELOCITY_CONTROL
    
    left_vel_multiplier  =  2
    right_vel_multiplier = -2
    
    #def __init__(self):
    
    
    def connect(self):
        try:
            self.odrv = odrive.find_any(timeout=5)

            print("\nConnected to ODrive: " + str(self.odrv.serial_number))
            print("HW version:  " + str(self.odrv.hw_version_major) + "." + str(self.odrv.hw_version_minor) + " - " + str(self.odrv.hw_version_variant))
            print("FW version:  " + str(self.odrv.fw_version_major) + "." + str(self.odrv.fw_version_minor) + "." + str(self.odrv.fw_version_revision))
            print("API version: " + odrive.version.get_version_str())
            print("Voltage:     " + str(self.odrv.vbus_voltage))
            
            self.left_axis = self.odrv.axis0
            self.right_axis = self.odrv.axis1

            self.odrv.config.brake_resistance = self.brake_resistance
            self.odrv.config.max_regen_current = self.max_regen_current
            self.odrv.config.dc_max_negative_current = self.dc_max_negative_current

            self.right_axis.motor.config.resistance_calib_max_voltage = self.left_axis.motor.config.resistance_calib_max_voltage = self.motor_resistance_calib_max_voltage
            self.right_axis.motor.config.calibration_current = self.left_axis.motor.config.calibration_current = self.motor_calibration_current
            self.right_axis.motor.config.pole_pairs = self.left_axis.motor.config.pole_pairs = self.motor_pole_pairs
            self.right_axis.motor.config.motor_type = self.left_axis.motor.config.motor_type = self.motor_type
            self.right_axis.motor.config.current_lim = self.left_axis.motor.config.current_lim = self.motor_current_lim
            self.right_axis.motor.config.current_control_bandwidth = self.left_axis.motor.config.current_control_bandwidth = self.motor_current_control_bandwidth
                                                                        
            self.right_axis.encoder.config.cpr = self.left_axis.encoder.config.cpr = self.encoder_cpr
            self.right_axis.encoder.config.mode = self.left_axis.encoder.config.mode = self.encoder_mode
                                                                        
            self.right_axis.controller.config.vel_limit = self.left_axis.controller.config.vel_limit = self.controller_vel_limit
            self.right_axis.controller.config.vel_gain = self.left_axis.controller.config.vel_gain = self.controller_vel_gain
            self.right_axis.controller.config.vel_integrator_gain = self.left_axis.controller.config.vel_integrator_gain = self.controller_vel_integrator_gain
            self.right_axis.controller.config.control_mode = self.left_axis.controller.config.control_mode = self.controller_control_mode
                                                                        
            self.right_axis.error = self.left_axis.error = 0
            self.right_axis.motor.error = self.left_axis.motor.error = 0
            self.right_axis.encoder.error = self.left_axis.encoder.error = 0
            self.right_axis.controller.error = self.left_axis.controller.error = 0
        except:
            print("Failed to connect to ODrive.")
            return False
        
        return True
    
    def calibrate(self):
        if not self.odrv:
            print("calibrate: ODrive not connected!")
            return False
        
        try:
            if(self.left_axis.motor.is_calibrated == False or self.left_axis.encoder.is_ready == False or self.right_axis.motor.is_calibrated == False or self.right_axis.encoder.is_ready == False):
                print("\nCalibrating...")

                self.left_axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
                self.right_axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
                while(self.left_axis.current_state != 1):
                    time.sleep(0.2)
                while(self.right_axis.current_state != 1):
                    time.sleep(0.2)
            else:
                print("Already calibrated, skipping...")

            if not(self.left_axis.error == 0 and self.right_axis.error == 0):
                print("Error during calibration.")
                print("Error left:  " + hex(self.left_axis.error) + "  " + hex(self.left_axis.motor.error) + "  " + hex(self.left_axis.encoder.error) + "  " + hex(self.left_axis.controller.error))
                print("Error right: " + hex(self.right_axis.error) + "  " + hex(self.right_axis.motor.error) + "  " + hex(self.right_axis.encoder.error) + "  " + hex(self.right_axis.controller.error))
            else:
                print("Calibration successful. Entering closed-loop control.")
        except:
            print("calibrate: Exception occured!")
            return False

        return True

    def engage(self):
        if not self.odrv:
            print("engage: ODrive not connected!")
            return False
        
        try:
            self.right_axis.controller.input_vel = 0
            self.right_axis.requested_state = 8
            self.left_axis.controller.input_vel = 0
            self.left_axis.requested_state = 8

            self.right_axis.config.enable_watchdog = True
            self.right_axis.config.watchdog_timeout = 0.2
            self.left_axis.config.enable_watchdog = True
            self.left_axis.config.watchdog_timeout = 0.2
        except:
            print("engage: Exception occured!")
            return False

        return True
    
    def disengage(self):
        if not self.odrv:
            print("disengage: ODrive not connected!")
            return False
        
        try:
            self.right_axis.requested_state = 1
            self.left_axis.requested_state = 1
            self.right_axis.config.enable_watchdog = False
            self.left_axis.config.enable_watchdog = False
        except:
            print("disengage: Exception occured!")
            return False

        return True
    
    def set_velocity(self, left_vel, right_vel):
        if not self.odrv:
            print("set_velocity: ODrive not connected!")
            return False
        
        try:
            self.left_axis.controller.input_vel = left_vel * self.left_vel_multiplier
            self.right_axis.controller.input_vel = right_vel * self.right_vel_multiplier
            self.left_axis.watchdog_feed()
            self.right_axis.watchdog_feed()
        except:
            print("set_velocity: Exception occured!")
            return False

        return True

    def update(self):
        if not self.odrv:
            print("update: ODrive not connected!")
            return False
        
        try:
            if not(self.left_axis.error == 0 and self.right_axis.error == 0):
                print("Error left:  " + hex(self.left_axis.error) + "  " + hex(self.left_axis.motor.error) + "  " + hex(self.left_axis.encoder.error) + "  " + hex(self.left_axis.controller.error))
                print("Error right: " + hex(self.right_axis.error) + "  " + hex(self.right_axis.motor.error) + "  " + hex(self.right_axis.encoder.error) + "  " + hex(self.right_axis.controller.error))
                self.left_axis.clear_errors()
                self.left_axis.requested_state = 8
                self.right_axis.clear_errors()
                self.right_axis.requested_state = 8
        except:
            print("update: Exception occured!")
            return False

        return True
    
    def get_vel(self):
        if not self.odrv:
            print("get_vel: ODrive not connected!")
            return False
        
        try:
            print(str(self.left_axis.encoder.vel_estimate * self.left_vel_multiplier) + "   " + str(self.right_axis.encoder.vel_estimate * self.right_vel_multiplier))
        except:
            print("get_vel: Exception occured!")
            return False

        return True
