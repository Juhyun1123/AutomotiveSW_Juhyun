"""Arrow-key Ackermann teleoperation in a Linux terminal."""
import math
import os
import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class KeyboardTeleop(Node):
    """Publish velocity commands with an inactivity stop."""

    def __init__(self):
        super().__init__('keyboard_teleop')
        self.declare_parameter('speed', 0.5)
        self.declare_parameter('steering_angle', 0.30)
        self.declare_parameter('key_timeout', 0.6)
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.speed = min(1.0, max(0.0, float(self.get_parameter('speed').value)))
        self.steer = min(0.40, max(0.0, float(self.get_parameter('steering_angle').value)))
        self.timeout = max(0.1, float(self.get_parameter('key_timeout').value))

    def publish(self, velocity, steering):
        msg = Twist()
        msg.linear.x = velocity
        msg.angular.z = velocity * math.tan(steering) / 0.40
        self.publisher.publish(msg)


def main(args=None):
    """Read complete terminal escape sequences and restore terminal on exit."""
    if not sys.stdin.isatty():
        print('Run keyboard_teleop in a separate interactive Ubuntu terminal.', file=sys.stderr)
        return
    rclpy.init(args=args)
    node = KeyboardTeleop()
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    velocity = steering = 0.0
    last_drive = last_steer = 0.0
    pending = b''
    pending_since = 0.0
    print('Up/Down: forward/reverse | Left/Right: steer | Space: stop | Q: quit')
    print('Hold arrows to repeat; steering alone does not move the car.')
    try:
        tty.setcbreak(fd)
        while rclpy.ok():
            now = time.monotonic()
            if select.select([fd], [], [], 0.05)[0]:
                pending += os.read(fd, 32)
                pending_since = now
            while pending:
                if pending.startswith(b'\x1b'):
                    if len(pending) < 3:
                        break
                    key, pending = pending[:3], pending[3:]
                else:
                    key, pending = pending[:1], pending[1:]
                if key in (b'\x1b[A', b'\x1bOA'):
                    velocity, last_drive = node.speed, now
                elif key in (b'\x1b[B', b'\x1bOB'):
                    velocity, last_drive = -node.speed, now
                elif key in (b'\x1b[D', b'\x1bOD'):
                    steering, last_steer = node.steer, now
                    if velocity:
                        last_drive = now
                elif key in (b'\x1b[C', b'\x1bOC'):
                    steering, last_steer = -node.steer, now
                    if velocity:
                        last_drive = now
                elif key == b' ':
                    velocity = steering = 0.0
                elif key.lower() == b'q':
                    return
            if pending and now - pending_since > 0.2:
                pending = b''
            if now - last_drive > node.timeout:
                velocity = 0.0
            if now - last_steer > node.timeout:
                steering = 0.0
            node.publish(velocity, steering)
            rclpy.spin_once(node, timeout_sec=0.0)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)
        if rclpy.ok():
            for _ in range(3):
                node.publish(0.0, 0.0)
                time.sleep(0.02)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
