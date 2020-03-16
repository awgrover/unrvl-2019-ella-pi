#!/usr/bin/env python3

# Monitor the arduino on the usb-port as serial,
# Based on the input, play a video:
# idle: 9-*.mp4 (actually, last by sort)
# The arduino should send 0+, 1+, etc when touched on a channel,
# and 0-, 1-, etc when released.
# We'll start a video called 0-*, 1-*, etc
# On the "-" we go back to idle

import glob, re, time, serial, os, psutil
from subprocess import Popen
from os import environ
from serial.tools.list_ports import comports

VideoDir = "movies"
MoviePattern = VideoDir + "/[0-9]*.mp4"
WaitForHello = 5 # seconds till arduino says hello
ArduinoHello = 'start' # from setup() time

FNULL = open(os.devnull,'w')

def collect_videos():
    # return a list of video file-names, in order
    # for 0..9*
    global VideoDir, MoviePattern
    return sorted(glob.glob(MoviePattern))

def arduino_port_name():
    # try to find the arduino
    # python3 -m serial.tools.list_ports -v
    for aport in comports():
        if environ.get('DEBUG'):
            print( "%s hwid:%s vid:%s desc:%s prod:%s iface:%s serial:%s mfg:%s" % (aport.device, aport.hwid, aport.vid, aport.description, aport.product, aport.interface, aport.serial_number, aport.manufacturer) )
        if  not aport.vid:
            # arduinos have to be USB, and that means a .vid
            pass #continue
        to_search = ' '.join(filter(None, [ aport.manufacturer, aport.product ]))
        # fixme: use the boards.txt from arduino-ide, and the vid/pid's
        if re.search('Arduino|Genuino|Lilypad', to_search, re.IGNORECASE) or environ.get('DEBUGUSEPORT'):
            print( "Arduino %s %s %s" % (aport.device, aport.manufacturer, aport.product) )
            return aport.device
    return None

def arduino_hello(port):
    start = time.time()
    # allow multiple reads
    while( (time.time() - start < WaitForHello) ):
        # i think arduinos tend to spit out extra crap before then re-start
        # so don't look for a clean "hello\n" 
        line = port.readline().decode('ascii')
        if re.search(ArduinoHello, line):
           hello = True
           print("saw '%s' in %5.2f secs" % (ArduinoHello, time.time() - start) )
           return True
        if environ.get('DEBUG') and line:
            print("> %s" % line)

    print("Didn't see '%s' in %5.2f secs" % (ArduinoHello, time.time() - start))
    return False

def touch_message(port):
    # the arduino will send lines
    # at the beginning of the line is +n or -n
    # (remember we still have a timeout)
    # we convert to:
    #           ( -1|0|1, n )
    # 0 means "no message"
    line = None
    if not environ.get('DEBUGUSEPORT'):
        line = port.readline().decode('ascii') 
    else:
        line = input("message: ")
    if not line:
        return (0,None)
    
    message = re.match('^([+-])(\d)', line)
    if not message:
        return (0,None)

    direction, n = message.group()
    n = int(n)
    direction = 1 if direction=='+' else -1
    return ( direction, n)

def get_procs(binary_name):
    procs = []
    for p in psutil.process_iter():
        if p.name() == binary_name:
            procs.append(p)
    return procs

def kill_procs(procs):
    for p in procs:
        p.kill()

def start_video( videos, video_number ):
    global FNUL

    # don't try if video_number won't work
    if len(videos) > 0 and video_number >= -1 and video_number < len(videos):
        old_players = get_procs('omxplayer.bin') # before we start new

        # the example made sure to start above the last one (layer++), but we don't
        cmd = "omxplayer --no-keys --layer %d %s "%(1,videos[video_number] )
        print( cmd )
        Popen(cmd, shell=True, stdout=FNULL,stderr=FNULL)

        kill_procs(old_players)
    else:
        print("No video %s in 0..%s" % ( video_number, len(videos) - 1) )

def main():
    print( "start\n" )

    # we'll assume that the last video is idle
    videos = collect_videos()
    print( videos )
    if not videos:
        print( "No videos: " + MoviePattern )
        exit(1)
    
    serial_port_name = arduino_port_name()
    if not serial_port_name:
        print( "Waiting for arduino to be plugged in...")
    while(not serial_port_name):
        serial_port_name = arduino_port_name()
        if not serial_port_name:
            time.sleep(0.1) # don't continously bash

    # timeout on the read before our WaitForHello timeout
    arduino = serial.Serial( serial_port_name, 115200, timeout=0.1 )

    print( "Waiting for arduino to say '%s'..." % ArduinoHello )
    if not (environ.get('DEBUGUSEPORT') or arduino_hello(arduino) ):
        exit(1)

    start_video( videos, -1 ) # aka idle

    last_direction = 0
    while True:
        direction, object_num = touch_message(arduino)
        print("! %s %s" % (direction, object_num) )

        # If we get two "touch" in a row, ignore the second one
        # If we get two "untouch" in a row, ignore the second one
        # So, "multi" touch is treated like the first (different) event
        if direction != last_direction and direction != 0:
            if direction > 0:
                start_video( videos, object_num )
            elif direction < 0:
                start_video( videos, -1 ) # aka idle
            last_direction = direction

    # install this as startup script

main()
