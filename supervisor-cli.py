#!/usr/bin/env python3

import logging
import os
import sys
import time
import argparse
import subprocess
import psutil
import datetime
import schedule

# Add some help and read parameters
parser=argparse.ArgumentParser(description=''' Small supervising daemon ''')
parser.add_argument('--proccess', default='sleep', help='Process to monitor. Default: sleep')
parser.add_argument('--command', default='sleep 20 &', help='Command to start daemon. Default: sleep 20')
parser.add_argument('--interval', type=int, default=3, help='Interval between checks in seconds. Default: 3')
parser.add_argument('--retry', type=int, default=3, help='Attempts to restart failed daemon. Default: 3')
parser.add_argument('--wait', type=int, default=3, help='Time to wait beetween restarts in seconds. Default: 3')
parser.add_argument('--log', default="no", help='Enable logging. Options: yes/no. Default: no')
args=parser.parse_args()

# Boolean: Check if process is running
def checkProcess(procName):
        for proc in psutil.process_iter():
            try:
                if procName in proc.name():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        return False;

# Void: Writes log files if logging is enabled
def logger(message):
        log = args.log.lower()
        now = datetime.datetime.now()
        print(str(now.strftime('%d-%m-%Y %H:%M:%S'))+": " + message)
        if log == "yes":
               logging.info(message)
        else:
              return
# Void: Runs check and restarts service
def check_run():
    # Load variables from config
    proc_name = args.proccess
    attempt = args.retry
    start_command = args.command
    time_wait = args.wait
    # Init counter
    current_attempt = 0
    # Is daemon alive? Then ok
    if  checkProcess(proc_name):
        logger(proc_name + " is running. Waiting...")
    # Ooops, daemon is dead. Let's try to restart it
    else:
        logger(proc_name + " is not running! restarting" )
        # Do not try so hard
        while current_attempt < attempt:
           logger("Restarting attempt: " + str(current_attempt+1) )
           logger("Running: " + start_command )
           # Wait between restarts
           if current_attempt > 0:
             time.sleep(time_wait)
           # Start it and get exit code
           p = subprocess.run(start_command, shell=True)
           logger("Start programm exit code: " + str(p.returncode) )
           # Bump counter
           current_attempt += 1
           # If daemon started and have not died after sucessful start - happines
           if p.returncode == 0 and checkProcess(proc_name):
               break
           # If not and we exausted all attempts - sadnes. requires restart to continue monitoring
           elif current_attempt >= attempt:
             logger("Failed to restart service")
             exit()

def main() -> None:
    # Set path to log and pid file
    logfile = os.path.join(os.getcwd(), "supervisor.log")
    interval_sec = args.interval
    run_schedule = True
    # Configure logging
    logging.basicConfig(filename=logfile,
                        level=logging.INFO,
                        datefmt='%d-%m-%Y %H:%M:%S',
                        format='%(asctime)s: %(message)s')

    # Start schedule with configured interval
    schedule.every(interval_sec).seconds.do(check_run)
    # While we still try to revive daemon - run scheduler
    while run_schedule:
      schedule.run_pending()

if __name__ == '__main__':
    main()
