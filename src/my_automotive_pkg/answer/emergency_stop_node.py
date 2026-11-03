#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    HistoryPolicy,
    DurabilityPolicy,
)

from sensor_msgs.msg import LaserScan


class EmergencyStopNode(Node):

    def __init__(self):
        super().__init__('emergency_stop_node')

        # 센서 데이터용 Best Effort QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            sensor_qos,
        )

        self.get_logger().info('Emergency Stop 노드가 시작되었습니다.')

    def scan_callback(self, msg: LaserScan):

        front_angle = math.radians(20.0)

        for i, distance in enumerate(msg.ranges):

            # 현재 인덱스에 해당하는 라이다 각도 계산
            angle = msg.angle_min + (i * msg.angle_increment)

            # 정면 ±20도가 아니면 검사하지 않음
            if abs(angle) > front_angle:
                continue

            # 유효하지 않은 거리값 제외
            if math.isnan(distance) or math.isinf(distance):
                continue

            if distance < msg.range_min or distance > msg.range_max:
                continue

            # 정면 1m 이내 장애물 발견
            if distance <= 1.0:
                red = '\033[91m'
                reset = '\033[0m'

                self.get_logger().warning(
                    f'{red}[EMERGENCY_STOP] 전방 장애물 감지!{reset}'
                )
                return


def main(args=None):
    rclpy.init(args=args)

    node = EmergencyStopNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()