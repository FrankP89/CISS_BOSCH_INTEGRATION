#!/usr/bin/env python

import roslib
import rospy
import tf
import std_msgs.msg
import sensor_msgs.msg
import geometry_msgs.msg
from collections import deque
from std_msgs.msg import Float64
from std_msgs.msg import UInt32
from geometry_msgs.msg import Quaternion, Vector3, PoseStamped
from sensor_msgs.msg import Temperature, RelativeHumidity, Illuminance, Imu

import serial, signal, ConfigParser, os, csv, time, math, numpy


# ROS init #
rospy.init_node('sensors')

pub_imu = rospy.Publisher('sensor_msgs/IMU', Imu, queue_size=5)
rospy.loginfo("Publishing Imu at: " + pub_imu.resolved_name)
pub_ps = rospy.Publisher('sensor_msgs/PoseStamped', PoseStamped, queue_size=5)

pub_temp = rospy.Publisher('sensor_msgs/Temperature',Temperature,queue_size=10)
pub_humi = rospy.Publisher('sensor_msgs/RelativeHumidity',RelativeHumidity,queue_size=10)
pub_lite = rospy.Publisher('sensor_msgs/Illuminance',Illuminance,queue_size=10)

pub_pres = rospy.Publisher('sensor_msgs/Pressure',Float64,queue_size=1)
pub_nois = rospy.Publisher('sensor_msgs/Noise',Float64,queue_size=1)


# General Variables #

MAX_VAL = 360
MIN_VAL = 0

acc_q = deque()
acc_l = deque()
gyr_q = deque()


# dataFileLocation = 'dataStream.csv'
# dataFileLocationEvent = 'detectedEvents.csv'
iniFileLocation = 'sensor.ini'
printInformation = True
printInformation_Conf = True

sensor_id_glbl = "sensor1"

# helper for signed 16bit conversion
def s16(value):
    return -(value & 0x8000) | (value & 0x7fff)

# helper for ini file parsing
def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

#configure acc range    
def config_acc_range(ser, acc_range):
    allowed_acc_ranges = [2,4,8,16]
    #only allow valid acc_ranges
    if acc_range in allowed_acc_ranges:
        print('set range of accel sensor to ' + str(acc_range) + 'g')
        conf_buff = bytearray([0xfe, 0x03, 0x80, 0x04, acc_range])
        write_conf(ser, conf_buff)               
    else:
        if printInformation_Conf: print('No valid acc_range given. CISS will operate with default or last valid value')

# crc calculation
def calc_crc(c_buff):
    result = 0
    for i in c_buff:
        result = result ^ i
    result = result ^ 254
    return result

# writes a string to the serial port with the possibility to
# have some debug output to stdout.
def write_conf(ser, conf_buf):
    v = calc_crc(conf_buf)
    conf_buf.append(v)
    conf_string = str(conf_buf)
    if printInformation_Conf: print("write config:"),
    for el in conf_string:
        if printInformation_Conf: print(hex(ord(el))),
    if printInformation_Conf: print
    ser.write(conf_string)
    time.sleep(0.2)						 # delay between 2 Commands to the CISS device 
    
# simple helper functions to parse the content of the payload
def parse_inert_vec(data):
    x = s16(data[0] | (data[1]<<8))
    y = s16(data[2] | (data[3]<<8))
    z = s16(data[4] | (data[5]<<8))
    array = [x, y, z]
    return array

def parse_temp(data):
    temp = s16(data[0] | (data[1]<<8))
    temp = float(temp)/10.0
    array = [temp]
    return array

def parse_press(data):
    press = data[0] | (data[1]<<8) | (data[2]<<16) | (data[3]<<24)
    press = float(press)/100
    array = [press]
    return array

def parse_humy(data):
    hum = s16(data[0] | (data[1]<<8))
    hum = float(hum)/100
    array = [hum]
    return array

def parse_light(data):
    light = data[0] | (data[1]<<8) | (data[2]<<16) | (data[3]<<24)
    array = [light]
    return array

def parse_aqu(data):
    aq = data[0] | (data[1]<<8)
    array = [aq]
    return array

def parse_enable(data):
    if printInformation:
        print("sensor:", hex(data[0]), "ack", "setup:", hex(data[1]))
    return []

def parse_disable(data):
    if printInformation:
        print("sensor:", hex(data[0]), "nack", "setup:", hex(data[1]))
    return []

def parse_event_detection(data):
    global sensor_id_glbl
    # Event detection frames are parsed here
    print "found event"
    print ' '.join([hex(i) for i in data[0:2]])
    sensorid = sensor_id_glbl
    Accel = data[0] & 0x03
    Gyro  = (data[0] & 0x0c) >> 2
    Mag   = (data[0] & 0X30) >> 4
    Temp  = (data[0] & 0xc0) >> 6
    Hum   = data[1] & 0x03
    Pressure = (data[1] & 0x0c) >> 2
    Light = (data[1] & 0x30) >> 4
    Noise = (data[1] & 0xc0) >> 6
    if Accel == 1: 
        write_to_csv_event(sensorid, "Accel : overshoot", int(time.time()*1000))
        if printInformation: print "Accel : overshoot"
    if Accel == 3: 
        write_to_csv_event(sensorid, "Accel : undershoot", int(time.time()*1000))
        if printInformation: print "Accel : undershoot"
    if Gyro == 1:
        write_to_csv_event(sensorid, "Gyro : overshoot", int(time.time()*1000))
        if printInformation: print "Gyro : overshoot"
    if Gyro == 3:
        write_to_csv_event(sensorid, "Gyro : undershoot", int(time.time()*1000))
        if printInformation: print "Gyro : undershoot"
    if Mag == 1:
        write_to_csv_event(sensorid, "Mag : overshoot", int(time.time()*1000))
        if printInformation: print "Mag : overshoot"
    if Mag == 3:
        write_to_csv_event(sensorid, "Mag : undershoot", int(time.time()*1000))
        if printInformation: print "Mag : undershoot"
    if Temp == 1:
        write_to_csv_event(sensorid, "Temp : overshoot", int(time.time()*1000))
        if printInformation: print "Temp : overshoot"
    if Temp == 3: 
        write_to_csv_event(sensorid, "Temp : undershoot", int(time.time()*1000))
        if printInformation: print "Temp : undershoot"
    if Hum == 1:
        write_to_csv_event(sensorid, "Hum : overshoot", int(time.time()*1000))
        if printInformation: print "Hum : overshoot"
    if Hum == 3:
        write_to_csv_event(sensorid, "Hum : undershoot", int(time.time()*1000))
        if printInformation: print "Hum : undershoot"
    if Pressure == 1: 
        write_to_csv_event(sensorid, "Pressure : overshoot", int(time.time()*1000))
        if printInformation: print "Pressure : overshoot"
    if Pressure == 3:
        write_to_csv_event(sensorid, "Pressure : undershoot", int(time.time()*1000))
        if printInformation: print "Pressure : undershoot"
    if Light == 1:
        write_to_csv_event(sensorid, "Light : overshoot", int(time.time()*1000))
        if printInformation: print "Light : overshoot"
    if Light == 3:
        write_to_csv_event(sensorid, "Light : undershoot", int(time.time()*1000))
        if printInformation: print "Light : undershoot"
    if Noise == 1:
        write_to_csv_event(sensorid, "Noise : overshoot", int(time.time()*1000))
        if printInformation: print "Noise : overshoot"
    if Noise == 3:
        write_to_csv_event(sensorid, "Noise : undershoot", int(time.time()*1000))
        if printInformation: print "Noise : undershoot"
    data = data[2:]

    return []

# Very simple class as a container for eache sensor with its id in the payload stream data_idx
# and the corresponding length of the subsequent data (e.g. 6 bytes for 2b xyz-vector)
class Sensor:
    def __init__(self, t, d, p, a, b):
        self.data_idx = t
        self.data_length = d
        self.parser = p
        self.parse_begin = a
        self.parse_end = b

    def parse(self, data):
        res = self.parser(data)
        if res == []:
            return []

        mask = ['', '', '', '', '', '', '', '', '', '', '', '', '', '']
        for i in range(self.parse_begin, self.parse_end):
            mask[i] = res[i - self.parse_begin]
        return mask

# Configuration of the different streaming modes. This is separated from the sensor class
# because the environmental information is clustered and not every parameter can be configured
# individually for each sensor.
class StreamingConfig:
    def __init__(self, t, i, e, p, c, l):
        # environmental or inertial streaming
        self.streaming_type = t
        self.streaming_id = i
        self.streaming_enabled = e
        self.streaming_period = p
        self.cfg_id = c
        self.cfg_length = l

    def enable(self, ser, flag = True):
        conf_buff = bytearray([0xfe, 2])
        conf_buff.append(self.streaming_id)
        if flag: conf_buff.append(1)
        else: conf_buff.append(0)
        write_conf(ser, conf_buff)

    def disable(self, ser):
        self.enable(ser, False)

    def configure(self, ser, flgSetSamplingRateOnly):
        if ((self.streaming_enabled or flgSetSamplingRateOnly) and self.streaming_period>0):
            if printInformation_Conf: print("configure period:",self.streaming_period)
                       
            conf_buff = bytearray([0xfe, self.cfg_length])
            conf_buff.append(self.cfg_id)
            conf_buff.append(2)
            k=0
            while ((len(conf_buff)-2) < self.cfg_length):
                conf_buff.append(self.streaming_period >> (k*8) & 0xff)
                k+=1

            write_conf(ser, conf_buff)
        if (self.streaming_enabled and (self.streaming_period>0) and (flgSetSamplingRateOnly==0)):  
            self.enable(ser)
        
    

# Configuration of the different event modes. This is separated from the sensor class
# because the event information can be configured individually for each sensor
class EventConfig:
    def __init__(self, t, i, e, evt, l, cmd):
        self.event_type = t
        self.event_id = i
        self.event_enabled = e
        self.event_threshold = evt
        self.cfg_length = l
        self.event_cmd = cmd
        self.enabled = 0

    def enable(self, ser, flag = True):
        conf_buff = bytearray([0xfe, 0x02, 0xfc])
        if flag: conf_buff.append(1)
        else: conf_buff.append(0)
        write_conf(ser, conf_buff)

    def disable(self, ser):
        self.enable(ser, False)

    def configure(self, ser):
        if self.event_enabled:
            self.enabled = 1
            for i in range(len(self.event_threshold)):
                if printInformation_Conf: print ("configure",self.event_type,"with",self.event_threshold[i])
                # set Event detection threshold
                conf_buff = bytearray([0xfe, (self.cfg_length[i] +2), self.event_id, self.event_cmd[i]])
                if (self.event_cmd[i] == 7): #handle temperature threshold separately, as value can be negative
                    if (self.event_threshold[i] > 127):
                        conf_buff.append(127)
                        if printInformation_Conf: print('Temperature limited to 127' )
                    elif (self.event_threshold[i] < -128):
                        conf_buff.append(128)
                        if printInformation_Conf: print('Temperature limited to -128' )
                    else:
                        conf_buff.append((256 + self.event_threshold[i])%256)            
                else:    
                    for j in range(self.cfg_length[i]):
                       conf_buff.append((int(self.event_threshold[i]) >> (j*8)) & 0xff)
                write_conf(ser, conf_buff)
 


def check_payload(payload):
    eval = 0
    for ind in range(len(payload)-1):
        eval = eval ^ payload[ind]

    if eval == payload[len(payload)-1]:
        return 1
    else:
        return 0

def conv_data(data):
    a = []
    for ind in range(len(data)):
        a.insert(ind, ord(data[ind]))
    return a


def normalize_accelerometer(val, min_val, max_val):
    val_between_0_and_1 = (val - min_val) / (abs(min_val) + abs(max_val))
    val_between_minus_1_and_1 = (val_between_0_and_1 * 2.0) - 1.0
    return val_between_minus_1_and_1


def fix_accelerometer(val):
    return normalize_accelerometer(val, MIN_VAL, MAX_VAL)


def frame_conversion(p,q,r,message):
    quat = Quaternion()
    quat_fixed = Quaternion()
    if (message == 'magnetometer'):
        if not p == '':        
	    p_ = float(p)/60*180
            if (p_ > 180):
                p = 180    
            if (p_ < -180):
                p = -180            
            p_ = math.radians(p_)
    
        if not p == '' and not q == '' and not r == '':
            quat = tf.transformations.quaternion_from_euler(0,0,p_) 

    if (message == 'gyro'):
        if not p == '':        
	    p_ = float(p) 

        if not q == '':
            q_ = float(q)             
            
        if not r == '':
            r_ = float(r)            
                
        if not p == '' and not q == '' and not r == '':
            quat = tf.transformations.quaternion_from_euler(p_, q_, r_) 

    if (message == 'accelerometer'):
        if not p == '':        
	    p_ = float(p)
            p_ = p_*90/1024     
            p_ = math.radians(p_)

        if not q == '':
            q_ = float(q)
            q_ = q_*90/1024     
            q_ = math.radians(q_)

        if not r == '':
            r_ = float(r)
            r_ = r_/1024
            r_ = math.radians(r_)
    
        if not p == '' and not q == '' and not r == '':
            quat = tf.transformations.quaternion_from_euler(p_, 0, 0)    
            print(type(quat))            
            quat_fixed.x = fix_accelerometer(quat[0])
            quat_fixed.y = fix_accelerometer(quat[1])
            quat_fixed.z = fix_accelerometer(quat[2])
            quat_fixed.w = fix_accelerometer(quat[3])            
    return quat


# simple helper to write sensor data to a csv file
def write_to_csv(id, buff, tstamp):
    global dataFileLocation, linear_acc
    if len(buff) < 14:
        return
    global acc_q
    global gyr_q
    
    

    #if not os.path.exists(dataFileLocation):
    #    with open(dataFileLocation, "wb") as csvOpen:
    #        csvobj = csv.writer(csvOpen, dialect='excel')
    #        csvobj.writerow([" id ", " timestamp ", " ax ", " ay ", " az ",
    #                         " gx ", " gy ", " gz ", " mx ", " my ", " mz ",
    #                         " t ", " p ", " h ", " l ", " n "])

    #with open(dataFileLocation, "a") as csvOpen:
    #    csvobj = csv.writer(csvOpen, dialect='excel')
    #    csvobj.writerow([id, tstamp, buff[0], buff[1], buff[2], buff[3], buff[4], buff[5], buff[6],buff[7], buff[8], buff[9], buff[10], buff[11], buff[12], buff[13]])
    if printInformation: print(id, tstamp, buff[0], buff[1], buff[2], buff[3], buff[4], buff[5],buff[6], buff[7], buff[8], buff[9], buff[10], buff[11], buff[12], buff[13])
    br.sendTransform((0.0, 0.0, 0.0),
                     (0.0, 0.0, 0.0, 1.0),
                     rospy.Time.now(),
                     "base_sensor",
                     "base_link")
    if not buff[0] == '':
        
 
        linear_acc = geometry_msgs.msg.Vector3()
        linear_acc.x = float(math.radians(float(buff[0])/1.8107))
        linear_acc.y = float(math.radians(float(buff[1])/1.8107))
        linear_acc.z = float(math.radians(float(buff[2])/1.8107))
        print("linear acc: ", linear_acc)
        acc_l.append(linear_acc)  
        
	quaternion_acc = frame_conversion(linear_acc.x,linear_acc.y,linear_acc.z, "accelerometer")
        br.sendTransform((0.0, 0.0, 0.05),
                         (quaternion_acc[0], quaternion_acc[1], quaternion_acc[2], quaternion_acc[3]),
                         rospy.Time.now(),
                         "accelerometer",
                         "base_sensor")
        
        	
    if not buff[3] == '':
        
        
        angular_vel = geometry_msgs.msg.Vector3()
        angular_vel.x = float(math.radians(float(buff[3])/1))
        angular_vel.y = float(math.radians(float(buff[4])/1))
        angular_vel.z = float(math.radians(float(buff[5])/1))        
        gyr_q.append(angular_vel)  

        quaternion_gyr = frame_conversion(angular_vel.x,angular_vel.y,angular_vel.z, "gyro")
        br.sendTransform((0.0, 0.0, 0.05),
                         (quaternion_gyr[0], quaternion_gyr[1], quaternion_gyr[2], quaternion_gyr[3]),
                         rospy.Time.now(),
                         "gyroscope",
                         "base_sensor")

    if not buff[6] == '':
        quaternion_mag = frame_conversion(buff[6],buff[7],buff[8], "magnetometer")
        br.sendTransform((0.0, 0.0, 0.05),
                         (quaternion_mag[0], quaternion_mag[1], quaternion_mag[2], quaternion_mag[3]),
                         rospy.Time.now(),
                         "magnetometer",
                         "base_sensor")

        orientation = geometry_msgs.msg.Quaternion()        
        orientation.x = (quaternion_mag[0])
        orientation.y = (quaternion_mag[1])
        orientation.z = (quaternion_mag[2])
        orientation.w = (quaternion_mag[3])
        acc_q.append(orientation)

    print (gyr_q)
    if (gyr_q and acc_q and acc_l):
        i = Imu()
        i.header.stamp = rospy.Time.now()
        i.header.frame_id = 'base_sensor'
        i.header.seq = UInt32(i.header.seq + 1)
        i.orientation = acc_q.pop()
        i.angular_velocity = gyr_q.pop()
        i.linear_acceleration = acc_l.pop()
        pub_imu.publish(i)

        ps = PoseStamped()
        ps.header = i.header
        ps.pose.orientation = i.orientation
        pub_ps.publish(ps)

    else:
        print ("empty deque")

    if not buff[9] == '':
        h = std_msgs.msg.Header()
        h.seq = UInt32(h.seq + 1)
        h.stamp = rospy.Time.now()
        h.frame_id = "base_sensor"
        temp = sensor_msgs.msg.Temperature()
        temp.header = h
        temp.temperature = (buff[9])
        temp.variance = (0.0)	
        pub_temp.publish(temp)
    if not buff[11] == '':
        h = std_msgs.msg.Header()
        h.seq = UInt32(h.seq + 1)
        h.stamp = rospy.Time.now()
        h.frame_id = "base_sensor"
        humi = sensor_msgs.msg.RelativeHumidity()
        humi.header = h
        humi.relative_humidity = (buff[11]/10.0)
        humi.variance = (0.0)	
        pub_humi.publish(humi)
    if not buff[10] == '':
        pub_pres.publish(buff[10])
    if not buff[12] == '':
        h = std_msgs.msg.Header()
        h.seq = UInt32(h.seq + 1)
        h.stamp = rospy.Time.now()
        h.frame_id = "base_sensor"
        lite = sensor_msgs.msg.Illuminance()
        lite.header = h
        lite.illuminance = (buff[12])
        lite.variance = (0.0)	
        pub_lite.publish(lite)
    if not buff[13] == '':
        pub_nois.publish(buff[13])



def write_to_csv_event(id, event, tstamp):
    global dataFileLocationEvent
    if not os.path.exists(dataFileLocationEvent):
        with open(dataFileLocationEvent, "wb") as csvOpen:
            csvobj = csv.writer(csvOpen, dialect='excel')
            csvobj.writerow([" id ", " timestamp ", "Event"])
    with open(dataFileLocationEvent, "a") as csvOpen:
        csvobj = csv.writer(csvOpen, dialect='excel')
        csvobj.writerow([id, tstamp, event])
           
out = 0

class CISSNode:
    def __init__(self):
        #initialize classes, dictionaries and variables
        self.flgEventEnabled = 0
        no_sens = Sensor(0, 0, parse_enable, 0, 0)
        enable = Sensor(1, 2, parse_enable, 0, 0)
        acc = Sensor(2, 6, parse_inert_vec, 0, 3)
        mag = Sensor(3, 6, parse_inert_vec, 6, 9)
        gyro = Sensor(4, 6, parse_inert_vec, 3, 6)
        temp = Sensor(5, 2, parse_temp, 9, 10)
        press = Sensor(6, 4, parse_press, 10, 11)
        humy = Sensor(7, 2, parse_humy, 11, 12)
        light = Sensor(8, 4, parse_light, 12, 13)
        aqu = Sensor(9, 2, parse_aqu, 13, 14)
        disable = Sensor(255, 2, parse_enable, 0, 0)
        event_detection = Sensor(0x7A, 2, parse_event_detection, 0, 0)
        self.sensorlist = [no_sens, acc, mag, gyro, temp, press, humy, light, aqu, enable, disable, event_detection]

        streaming_acc = StreamingConfig("inertial_acc", 0x80, True,   100000, 0x80, 6)
        streaming_gyr = StreamingConfig("inertial_gyr", 0x82, False,  100000, 0x82, 6)
        streaming_mag = StreamingConfig("inertial_mag", 0x81, False,  100000, 0x81, 6)
        streaming_env = StreamingConfig("inertial_env", 0x83, False, 1000000, 0x83, 4)
        # light sensor 
        streaming_light = StreamingConfig("inertial_lig", 0x84, False, 1000000, 0x84, 4)
        self.streaminglist = {"env": streaming_env, 
                              "acc": streaming_acc,
                              "mag": streaming_mag, 
                              "gyr": streaming_gyr,
                              "light": streaming_light}
        event_acc = EventConfig("event_acc", 0x80, False, [0], [2], [3])
        event_gyr = EventConfig("event_gyr", 0x82, False, [0], [2], [3])
        event_mag = EventConfig("event_mag", 0x81, False, [0], [2], [3])
        event_env = EventConfig("event_env", 0x83, False, [0,0,0], [1,1,3], [7,8,9])
        event_noise = EventConfig("event_noise", 0x85, False, [0], [2], [3])
        event_light = EventConfig("event_light", 0x84, False, [0], [3], [3])
        self.eventlist = {"env": event_env, 
                          "acc": event_acc,
                          "mag": event_mag, 
                          "gyr": event_gyr,
                          "noise": event_noise,
                          "light": event_light }
        self.acc_range = 0

        # read valus from ini file
        self.get_ini_config()
        
        # connect to COM port
        self.connect()
        
        self.checkEventEnabled()
        # disable all sensors before configuration
        self.disable_sensors()
        
        # configure the sensors as given in the sensor.ini file  
        self.config_sensors()

    def get_ini_config(self):
        global sensor_id_glbl
        global iniFileLocation

        if not os.path.exists(iniFileLocation):
            sIRConf = ConfigParser.ConfigParser()       
            sIRConf.add_section("sensorcfg")
            sIRConf.set("sensorcfg", "sensorid", "Ciss1")
            sIRConf.set("sensorcfg", "acc_stream", "true")
            sIRConf.set("sensorcfg", "acc_event", "false")
            sIRConf.set("sensorcfg", "acc_threshold", "0")
            sIRConf.set("sensorcfg", "acc_range", "16")
            sIRConf.set("sensorcfg", "gyr_stream", "true")
            sIRConf.set("sensorcfg", "gyr_event", "false")
            sIRConf.set("sensorcfg", "gyr_threshold", "0")
            sIRConf.set("sensorcfg", "mag_stream", "true")
            sIRConf.set("sensorcfg", "mag_event", "false")
            sIRConf.set("sensorcfg", "mag_threshold", "0")
            sIRConf.set("sensorcfg", "period_inert_us", "100000")
            sIRConf.set("sensorcfg", "env_stream", "true")
            sIRConf.set("sensorcfg", "env_event", "false")
            sIRConf.set("sensorcfg", "temp_threshold", "0")
            sIRConf.set("sensorcfg", "hum_threshold", "0")
            sIRConf.set("sensorcfg", "pres_threshold", "0")
            sIRConf.set("sensorcfg", "light_stream", "true")
            sIRConf.set("sensorcfg", "light_event", "false")
            sIRConf.set("sensorcfg", "light_threshold", "0")
            sIRConf.set("sensorcfg", "noise_event", "false")
            sIRConf.set("sensorcfg", "noise_threshold", "0")
            sIRConf.set("sensorcfg", "period_env_us", "1000000")
            sIRConf.set("sensorcfg", "port", "/dev/ttyACM0")

            with open(iniFileLocation, "w") as newcfgfile:
                sIRConf.write(newcfgfile)

        snIniConfig = ConfigParser.ConfigParser()
        snIniConfig.read(iniFileLocation)
        self.sensorid = snIniConfig.get("sensorcfg", "sensorid")
        sensor_id_glbl = self.sensorid
        sample_period_inert_us = int(snIniConfig.get("sensorcfg", "period_inert_us"))
        sample_period_env_us = int(snIniConfig.get("sensorcfg", "period_env_us"))/1000000        
        self.port = snIniConfig.get("sensorcfg", "port")
        self.streaminglist["env"].streaming_enabled = str2bool(snIniConfig.get("sensorcfg", "env_stream"))
        self.streaminglist["acc"].streaming_enabled = str2bool(snIniConfig.get("sensorcfg", "acc_stream"))
        self.streaminglist["mag"].streaming_enabled = str2bool(snIniConfig.get("sensorcfg", "mag_stream"))
        self.streaminglist["gyr"].streaming_enabled = str2bool(snIniConfig.get("sensorcfg", "gyr_stream"))
        self.streaminglist["light"].streaming_enabled = str2bool(snIniConfig.get("sensorcfg", "light_stream"))

        self.eventlist["env"].event_enabled = str2bool(snIniConfig.get("sensorcfg", "env_event"))
        self.eventlist["env"].event_threshold = [int(snIniConfig.get("sensorcfg", "temp_threshold")),
                                                 int(snIniConfig.get("sensorcfg", "hum_threshold")),
                                                 int(snIniConfig.get("sensorcfg", "pres_threshold"))]
        self.eventlist["acc"].event_enabled = str2bool(snIniConfig.get("sensorcfg", "acc_event"))
        self.eventlist["acc"].event_threshold = [int(snIniConfig.get("sensorcfg", "acc_threshold"))]
        self.eventlist["mag"].event_enabled = str2bool(snIniConfig.get("sensorcfg", "mag_event"))
        self.eventlist["mag"].event_threshold = [int(snIniConfig.get("sensorcfg", "mag_threshold"))]
        self.eventlist["gyr"].event_enabled = str2bool(snIniConfig.get("sensorcfg", "gyr_event"))
        self.eventlist["gyr"].event_threshold = [int(snIniConfig.get("sensorcfg", "gyr_threshold"))]
        self.eventlist["light"].event_enabled = str2bool(snIniConfig.get("sensorcfg", "light_event"))
        self.eventlist["light"].event_threshold = [int(snIniConfig.get("sensorcfg", "light_threshold"))]
        #noise is not actually not streamed over USB 
        self.eventlist["noise"].event_enabled = str2bool(snIniConfig.get("sensorcfg", "noise_event"))
        self.eventlist["noise"].event_threshold = [int(snIniConfig.get("sensorcfg", "noise_threshold"))]
        self.streaminglist["env"].streaming_period = sample_period_env_us
        self.streaminglist["light"].streaming_period = sample_period_env_us
        self.streaminglist["acc"].streaming_period = sample_period_inert_us
        self.streaminglist["mag"].streaming_period = sample_period_inert_us
        self.streaminglist["gyr"].streaming_period = sample_period_inert_us
        self.acc_range = int(snIniConfig.get("sensorcfg", "acc_range"))


    def connect(self):
        self.ser = serial.Serial(self.port,baudrate=115200,timeout=1)

    def checkEventEnabled(self):
        for elem in self.eventlist.itervalues():
            if elem.event_enabled == 1:
                self.flgEventEnabled = 1

    def disconnect(self):
        self.disable_sensors()
        self.ser.close()

    def disable_sensors(self):
        self.ser.flush()

        # Disable all enabled sensors exept for accel since it in the special mode of 2K streaming,
        # diabling the accel will trigger a node reset. Therefore, no serial port operations
        # will be possible until the node reboots and thus the accel disable should be sent the
        # last. This is introduced with v02.01.00
        #
        for elem in self.streaminglist.itervalues():
            if elem.streaming_enabled and elem !=self.streaminglist["acc"]:
                elem.disable(self.ser)

        if (self.flgEventEnabled == 1):
            conf_buff = bytearray([0xfe, 0x02, 0xfc, 0x00])
            write_conf(self.ser, conf_buff)

        #If 2KHz streaming is enabled, the following will trigger a reset    
        if self.streaminglist["acc"].streaming_enabled :      
            self.streaminglist["acc"].disable(self.ser)
            
    def enable_sensors(self):
        for elem in self.streaminglist.itervalues():
            if elem.streaming_enabled:
                elem.enable(self.ser)
        for elem in self.eventlist.itervalues():
            if elem.event_enabled:
                elem.enable(self.ser)

    def get_type(self, num):
        a = -1
        for i in range(len(self.sensorlist)):
            if num == self.sensorlist[i].data_idx:
                a = i
        return a

    def parse_payload(self, payload):
        payload.pop(0)
        payload.pop(len(payload)-1)
        while len(payload) != 0:
            t = self.get_type(payload[0])
            payload.pop(0)
            if t >= 0:
                    mask = self.sensorlist[t].parse(payload[0:self.sensorlist[t].data_length])
                    write_to_csv(self.sensorid, mask, int(time.time()*1000))
                    payload = payload[self.sensorlist[t].data_length:]
            else:
                break

    def stream(self):
        global out
    
        sof = "\xFE"
        data = []
        sub_payload = []
        payload_found = 0
        payload = []
        sr = self.ser
        while  payload_found != 1:
            while not out == sof:
                out = sr.read()
    
            length = sr.read()
            if length:
                length = ord(length)
            else:
                continue
            buffer = sr.read(length+1)
            payload = conv_data(buffer)
            payload.insert(0, length)
            out = ""
            if check_payload(payload) == 1:
                payload_found = 1
                self.parse_payload(payload)

    def config_sensors(self):
        # Configure range of acc if acc streaming or threshold detection is enabled
        # As long as only acc sensor can has a configurable range his will not be 
        # handled by a separate method of StreamingConfig or EventConfig 
        
        if (self.eventlist["acc"].event_enabled or self.streaminglist["acc"].streaming_enabled): 
            config_acc_range(self.ser, self.acc_range)       
                        
        # flag to signal if any event is configured
        flgAnyEventConfigured = 0
        
        #check if one of the inertial sensors is enabled in event detection mode, if yes set the sample period
        if (self.eventlist["acc"].event_enabled or self.eventlist["mag"].event_enabled or self.eventlist["gyr"].event_enabled):
            self.streaminglist["acc"].configure(self.ser, 1)
            flgAnyEventConfigured = 1
        #check if env, light or noise is enabled in event detection mode, if yes set the sample period 
        if (self.eventlist["env"].event_enabled or self.eventlist["light"].event_enabled or self.eventlist["noise"].event_enabled):            
            self.streaminglist["env"].configure(self.ser, 1)
            flgAnyEventConfigured = 1
 
        #configure the sensors for datastreaming only if no event detection mode is configured for any of the sensors
        if flgAnyEventConfigured==0:
            for elem in self.streaminglist.itervalues():
                elem.configure(self.ser, 0)
           
        for elem in self.eventlist.itervalues():
            elem.configure(self.ser)   

        #send the start event detection mode only at the end of the event mode configuration (i.e. respective thresholds)
        if flgAnyEventConfigured == 1:            
            self.eventlist["acc"].enable(self.ser)   #enabling of the event mode, therefore use "acc" instance, 
            

def ctrl_c_handler(signal, frame,node):
    raise Exception("")

node = CISSNode()

def main():
    signal.signal(signal.SIGINT, ctrl_c_handler)
    
    while 1:
        node.stream()

if __name__ == "__main__":
    #try:
        #rospy.init_node('fixed_tf_broadcaster')
        br = tf.TransformBroadcaster()
        rate = rospy.Rate(10.0)
        main()
    #except Exception as e: 
        #if printInformation: print("disconnected")
        #node.disconnect()
        #time.sleep(1)
        #exit(0)

