import logging
import time

from buildhat import Motor

log = logging.getLogger(__name__)


class MotorController:

    def __init__(self, motor_ports, rate=-1):
        self._motor_x = Motor(motor_ports[0])
        self._motor_y = Motor(motor_ports[1])
        # self.motor_x.set_speed_unit_rpm(True)

        self._rate = rate  # commands per second

        self._x_movement = 'stop'
        self._y_movement = 'stop'
        self._last_command = 0
        self._target = (0, 0)

    def move_to_middle(self,
                       frame_middle,
                       detection_middle,
                       hor_tolerance=0.2,
                       ver_tolerance=0.2,
                       hor_speed=12,
                       ver_speed=3):
        # move motors to keep detection middle in middle of frame
        if self._target == detection_middle:
            return

        if self._rate > 0 and time.time() < self._last_command + 1 / self._rate:
            return

        hor_tol_abs = frame_middle[0] * hor_tolerance
        if frame_middle[0] > detection_middle[0] + hor_tol_abs:
            if not self._x_movement == 'right':
                log.info('move right')
                self._x_movement = 'right'
                # self.motor_x.start(-hor_speed)
                # self.motor_x.pwm(-0.5)
                # time.sleep(0.03)
                self._motor_x.pwm(-hor_speed / 100)
        elif frame_middle[0] < detection_middle[0] - hor_tol_abs:
            if not self._x_movement == 'left':
                log.info('move left')
                self._x_movement = 'left'
                # self.motor_x.start(hor_speed)
                # self.motor_x.pwm(0.5)
                # time.sleep(0.03)
                self._motor_x.pwm(hor_speed / 100)
        else:
            if not self._x_movement == 'stop':
                log.info('stop horizontal')
                self._x_movement = 'stop'
                # self.motor_x.start(0)
                # self.motor_x.stop()
                self._motor_x.pwm(0)

        ver_tol_abs = frame_middle[1] * ver_tolerance
        if frame_middle[1] > detection_middle[1] + ver_tol_abs:
            if not self._y_movement == 'up':
                log.info('move up')
                self._y_movement = 'up'
                # self.motor_y.start(-ver_speed)
                self._motor_y.pwm(-ver_speed / 100)
        elif frame_middle[1] < detection_middle[1] - ver_tol_abs:
            if not self._y_movement == 'down':
                log.info('move down')
                self._y_movement = 'down'
                # self.motor_y.start(ver_speed)
                self._motor_y.pwm(ver_speed / 100)
        else:
            if not self._y_movement == 'stop':
                log.info('stop vertical')
                self._y_movement = 'stop'
                # self.motor_y.start(0)
                # self.motor_y.stop()
                self._motor_y.pwm(0)

        self._target = detection_middle
        self._last_command = time.time()

    def to_position(self, x, y):
        log.info('to center')
        self._motor_x.run_to_position(x, blocking=False)
        self._motor_y.run_to_position(y, blocking=False)

    def stop(self):
        if not self._x_movement == 'stop':
            log.info('stop horizontal')
            self._x_movement = 'stop'
            self._motor_x.pwm(0)
            # self.motor_x.stop()

        if not self._y_movement == 'stop':
            log.info('stop vertical')
            self._y_movement = 'stop'
            self._motor_y.pwm(0)

        self._last_command = time.time()
