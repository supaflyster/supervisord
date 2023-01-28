#!/usr/bin/env python3

import logging
import os
import time
import argparse
import subprocess
import schedule
import psutil
from daemons import daemonizer

# Add some help and read parameters
parser = argparse.ArgumentParser(description=""" Small supervising daemon """)
parser.add_argument("action", help="Available actions: start/stop/restart")
parser.add_argument(
    "--process", default="sleep", help="Process to monitor. Default: sleep"
)
parser.add_argument(
    "--command", default="sleep 20 &", help="Command to start daemon. Default: sleep 20"
)
parser.add_argument(
    "--interval",
    type=int,
    default=3,
    help="Interval between checks in seconds. Default: 3",
)
parser.add_argument(
    "--retry", type=int, default=3, help="Attempts to restart failed daemon. Default: 3"
)
parser.add_argument(
    "--wait",
    type=int,
    default=3,
    help="Time to wait between restarts in seconds. Default: 3",
)
parser.add_argument(
    "--log", default="yes", help="Enable logging. Options: yes/no. Default: yes"
)
args = parser.parse_args()


# Boolean: Checks if process is running
def checkProcess(procName):
    for proc in psutil.process_iter():
        try:
            if procName in proc.name():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


# Void: Writes log files if logging is enabled
def logger(message):
    log = args.log.lower()
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
    if checkProcess(proc_name):
        logger(proc_name + " is running. Waiting...")
    # Oops, daemon is dead. Let's try to restart it
    else:
        logger(proc_name + " is not running! restarting")
        # Do not try so hard
        while current_attempt < attempt:
            logger("Restarting attempt: " + str(current_attempt))
            logger("Running: " + start_command)
            # Wait between restarts
            time.sleep(time_wait)
            # Start it and get exit code
            p = subprocess.run(start_command, shell=True)
            logger("Start program exit code: " + str(p.returncode))
            # Bump counter
            current_attempt += 1
            # If daemon started and have not died after successful start - happiness
            if p.returncode == 0 and checkProcess(proc_name):
                break
            # If not and we exhausted all attempts - sadness. requires restart to continue monitoring
            if current_attempt >= attempt:
                logger("Failed to restart service")
                # Break the loop
                run_schedule = False
                # Clear schedule
                schedule.clear()


# Void: Daemonized. Initializes scheduler with a check
@daemonizer.run(pidfile=os.path.join(os.getcwd(), "supervisor.pid"))
def run():
    # Read variables
    interval_sec = args.interval
    run_schedule = True
    # Start schedule with configured interval
    schedule.every(interval_sec).seconds.do(check_run)
    # While we still try to revive daemon - run scheduler
    while run_schedule:
        schedule.run_pending()


def main() -> None:
    # Read command
    action = args.action
    # Configure logging
    logfile = os.path.join(os.getcwd(), "supervisor.log")
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        datefmt="%d-%m-%Y %H:%M:%S",
        format="%(asctime)s: %(message)s",
    )

    if action == "start":

        run()

    elif action == "stop":

        run.stop()

    elif action == "restart":

        run.stop()
        run()

    elif action == "coffee":
        art = """
                   )))
                   (((
                 +-----+
                 |     |]
                 `-----'
               ___________
               `---------'  """
        print(art)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
