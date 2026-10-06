#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오토모티브SW프로그래밍 5주차 실습 런치 파일: TF2 데모 시스템 통합 실행
작성자: 김동주 교수 (deekim@cu.ac.kr)

[설명]
정적 브로드캐스터(static_tf_broadcaster), 동적 브로드캐스터(dynamic_tf_broadcaster),
그리고 TF 버퍼 리스너(tf_listener) 세 노드를 단일 명령으로 동시에 실행하고
프로세스 수명주기를 관리하는 ROS 2 런치 파일입니다.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    ROS 2 Launch 프레임워크가 실행할 노드 목록을 담은 LaunchDescription을 반환합니다.
    """
    return LaunchDescription([
        # 1. 정적 변환 브로드캐스터 노드 실행
        # base_link -> lidar_link 오프셋(x: 0.5m, z: 0.3m)을 /tf_static으로 1회 발행
        Node(
            package='my_sensor_pkg',
            executable='static_tf',
            name='static_tf_broadcaster',
            output='screen'
        ),

        # 2. 동적 오도메트리 브로드캐스터 노드 실행
        # 원형 궤적 회전 주행에 따른 odom -> base_link 변환을 /tf로 30Hz 발행
        Node(
            package='my_sensor_pkg',
            executable='dynamic_tf',
            name='dynamic_tf_broadcaster',
            output='screen'
        ),

        # 3. TF2 버퍼 및 룩업 리스너 노드 실행
        # 10Hz 주기로 odom -> lidar_link 합성 변환을 버퍼에서 질의하여 터미널에 로깅
        Node(
            package='my_sensor_pkg',
            executable='tf_listener',
            name='tf_listener',
            output='screen'
        )
    ])
