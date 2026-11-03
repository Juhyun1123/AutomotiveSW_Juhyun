#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
강의명: 오토모티브SW프로그래밍
주차: 7주차
파일명: ackermann_controller.py
설명: Twist(/cmd_vel) 메시지를 구독하여 4륜 아커만 조향 각도 및 차동 휠 구동 속도로 변환하고,
      통신 단절 시 0.5초 이내에 차량을 자동으로 비상 정지시키는 안전 워치독(Watchdog) 내장 노드.
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray


class AckermannControllerNode(Node):
    """
    cmd_vel 토픽을 구독하여 아커만 조향 기구학을 연산하고
    좌/우 전륜 조향각과 좌/우 후륜 구동 속도를 액추에이터 토픽으로 발행하는 제어 노드
    """

    def __init__(self):
        super().__init__('ackermann_controller')

        # =====================================================================
        # 1. 차량 기구학 및 안전 제어 파라미터 선언 (외부 Launch 및 YAML에서 동적 변경 가능)
        # =====================================================================
        self.declare_parameter('wheelbase', 1.8)           # L: 축거 (앞바퀴축과 뒷바퀴축 사이 거리, 단위: m)
        self.declare_parameter('tread', 1.2)               # W: 윤거 (좌우 바퀴 중심 사이 거리, 단위: m)
        self.declare_parameter('max_steering_angle', 0.61) # 최대 조향각 (약 35도, 기계적 한계 보호, 단위: rad)
        self.declare_parameter('watchdog_timeout', 0.5)    # 통신 단절 판정 기준 시간 (단위: 초)
        self.declare_parameter('control_rate', 20.0)       # 확정적 제어 루프 주기 (단위: Hz, 20Hz = 50ms)

        # 파라미터 값 추출
        self.wheelbase = self.get_parameter('wheelbase').value
        self.tread = self.get_parameter('tread').value
        self.max_steer = self.get_parameter('max_steering_angle').value
        self.watchdog_timeout = self.get_parameter('watchdog_timeout').value
        self.control_rate = self.get_parameter('control_rate').value

        # =====================================================================
        # 2. QoS (통신 서비스 품질) 설정
        #    - 제어 명령은 패킷 누락을 방지하기 위해 반드시 RELIABLE 정책 사용
        # =====================================================================
        control_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE
        )

        # =====================================================================
        # 3. 토픽 퍼블리셔 및 서브스크라이버 생성
        # =====================================================================
        # 1) 입력: 키보드 teleop 또는 상위 내비게이션 노드의 속도 제어 명령 수신
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            control_qos
        )

        # 2) 출력: Gazebo 시뮬레이터 플러그인 또는 실제 모터 드라이버 제어 토픽
        #    배열 데이터 구조:
        #    - data[0]: 좌측 앞바퀴 조향각 (steer_left, rad)
        #    - data[1]: 우측 앞바퀴 조향각 (steer_right, rad)
        #    - data[2]: 좌측 뒷바퀴 선속도 (speed_rear_left, m/s)
        #    - data[3]: 우측 뒷바퀴 선속도 (speed_rear_right, m/s)
        self.actuator_pub = self.create_publisher(
            Float64MultiArray,
            '/vehicle/actuator_commands',
            control_qos
        )

        # =====================================================================
        # 4. 제어 내부 상태 변수 및 타이머 초기화
        # =====================================================================
        self.target_linear_v = 0.0          # 목표 전진 선속도 (m/s)
        self.target_angular_w = 0.0         # 목표 요잉 회전 각속도 (rad/s)
        self.last_cmd_time = self.get_clock().now()  # 마지막 명령 수신 시각 기록
        self.is_watchdog_triggered = False  # 안전 정지 상태 플래그

        # 20Hz 고정 주기 타이머 생성 (정기적인 기구학 연산 및 워치독 감시 수행)
        timer_period_sec = 1.0 / self.control_rate
        self.control_timer = self.create_timer(timer_period_sec, self.control_loop_callback)

        self.get_logger().info(
            f'=== 아커만 제어 노드 기동 완료 ===\n'
            f'  - 휠베이스(L): {self.wheelbase:.2f} m\n'
            f'  - 트레드(W): {self.tread:.2f} m\n'
            f'  - 최대 조향각: {math.degrees(self.max_steer):.1f} deg ({self.max_steer:.2f} rad)\n'
            f'  - 워치독 타임아웃: {self.watchdog_timeout:.2f} 초\n'
            f'  - 제어 루프 주기: {self.control_rate:.1f} Hz'
        )

    def cmd_vel_callback(self, msg: Twist):
        """
        비동기로 인입되는 cmd_vel 메시지 수신 콜백:
        - 최신 속도 명령을 버퍼에 저장하고 워치독 타임스탬프를 현재 시각으로 갱신
        """
        self.target_linear_v = msg.linear.x
        self.target_angular_w = msg.angular.z
        self.last_cmd_time = self.get_clock().now()

        # 워치독 정지 상태였다가 새 명령이 들어온 경우 정상 상태로 복구
        if self.is_watchdog_triggered:
            self.get_logger().info('새 제어 명령 수신: 워치독 안전 정지 해제 -> 정상 주행 재개')
            self.is_watchdog_triggered = False

    def control_loop_callback(self):
        """
        20Hz 확정적 주기로 반복 실행되는 핵심 제어 루프:
        1. 워치독 타임아웃 감시 (Fail-Safe)
        2. 아커만 조향 기하학 계산
        3. 액추에이터 제어 명령 퍼블리시
        """
        now = self.get_clock().now()
        elapsed_sec = (now - self.last_cmd_time).nanoseconds / 1e9

        # -------------------------------------------------------------
        # 1. 안전 워치독 감시 로직 (ISO 26262 기능안전 원칙 적용)
        # -------------------------------------------------------------
        if elapsed_sec > self.watchdog_timeout:
            if not self.is_watchdog_triggered:
                self.get_logger().warning(
                    f'[경고] 제어 명령 통신 단절 감지! (경과 시간: {elapsed_sec:.3f}초 > 임계치: {self.watchdog_timeout}초)\n'
                    f'      차량 폭주를 방지하기 위해 즉시 비상 정지(Fail-Safe) 모드로 전이합니다.'
                )
                self.is_watchdog_triggered = True

            # 비상 정지 명령 발행 (조향각 0 rad, 바퀴 속도 0 m/s)
            self.publish_actuators(0.0, 0.0, 0.0, 0.0)
            return

        # -------------------------------------------------------------
        # 2. 정상 상태: 아커만 조향 기구학 수학 연산
        # -------------------------------------------------------------
        steer_l, steer_r, speed_l, speed_r = self.compute_ackermann_kinematics(
            self.target_linear_v,
            self.target_angular_w
        )

        # -------------------------------------------------------------
        # 3. 제어 명령 퍼블리시
        # -------------------------------------------------------------
        self.publish_actuators(steer_l, steer_r, speed_l, speed_r)

    def compute_ackermann_kinematics(self, v: float, omega: float):
        """
        선속도 v (m/s)와 요잉 각속도 omega (rad/s)로부터
        좌/우 앞바퀴 조향각 및 좌/우 뒷바퀴 차동 속도를 계산하는 함수
        """
        # 1) 완전 직진 주행 조건 (회전 각속도가 0에 수렴하는 경우)
        if abs(omega) < 1e-5:
            return 0.0, 0.0, v, v

        # 2) 제자리 회전 시도 조건 (선속도가 0인데 각속도만 있는 경우)
        #    아커만 차량은 차동 구동 로봇과 달리 제자리 회전이 물리적으로 불가능함
        if abs(v) < 1e-5:
            self.get_logger().warning('아커만 구조는 선속도 0 상태에서의 제자리 회전이 불가능합니다.', throttle_duration_sec=2.0)
            return 0.0, 0.0, 0.0, 0.0

        # 3) 회전 반경 R = v / omega 계산 (뒷축 중심 기준 선회 반경)
        R = v / omega

        # 4) 아커만 기하학에 따른 내측/외측 바퀴 회전 반경 도출
        #    - 좌회전 (omega > 0): 좌측 바퀴가 내측(R - W/2), 우측 바퀴가 외측(R + W/2)
        #    - 우회전 (omega < 0): 우측 바퀴가 내측(R - W/2), 좌측 바퀴가 외측(R + W/2)
        if omega > 0:  # 좌회전
            R_left = R - (self.tread / 2.0)
            R_right = R + (self.tread / 2.0)
            steer_left = math.atan2(self.wheelbase, R_left)
            steer_right = math.atan2(self.wheelbase, R_right)
        else:          # 우회전
            R_left = R + (self.tread / 2.0)
            R_right = R - (self.tread / 2.0)
            steer_left = math.atan2(self.wheelbase, R_left)
            steer_right = math.atan2(self.wheelbase, R_right)

        # 5) 기계적 조향 한계 각도 클램핑 (하드웨어 서보 모터 보호)
        steer_left = max(-self.max_steer, min(self.max_steer, steer_left))
        steer_right = max(-self.max_steer, min(self.max_steer, steer_right))

        # 6) 좌우 후륜 구동 휠의 차동 속도 계산 (v_wheel = omega * R_wheel)
        speed_rear_left = omega * (R - self.tread / 2.0)
        speed_rear_right = omega * (R + self.tread / 2.0)

        return steer_left, steer_right, speed_rear_left, speed_rear_right

    def publish_actuators(self, steer_l: float, steer_r: float, speed_l: float, speed_r: float):
        """
        계산된 조향각 및 휠 속도를 Float64MultiArray 메시지로 패키징하여 발행
        """
        msg = Float64MultiArray()
        msg.data = [
            float(steer_l),
            float(steer_r),
            float(speed_l),
            float(speed_r)
        ]
        self.actuator_pub.publish(msg)


def main(args=None):
    """
    ROS 2 Python 진입점 함수
    """
    rclpy.init(args=args)
    node = AckermannControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('사용자 종료 요청(Ctrl+C)으로 노드를 안전하게 종료합니다.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
