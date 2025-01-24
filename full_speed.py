#!/usr/bin/env python3

from time import sleep
from ev3dev2.motor import OUTPUT_A, OUTPUT_B
from ev3_motor import EV3Motor


if __name__ == "__main__":
    motorL = EV3Motor(port=OUTPUT_A, motor_type='large')
    motorR = EV3Motor(port=OUTPUT_B, motor_type='large')

    motorL.set_speed(100)
    motorR.set_speed(100)

    while True:
        sleep(1)