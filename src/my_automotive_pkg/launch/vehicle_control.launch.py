#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
강의명: 오토모티브SW프로그래밍
주차: 7주차
파일명: vehicle_control.launch.py
설명: 아커만 조향 제어기 노드(ackermann_controller)와 시뮬레이션 파라미터를
      통합 기동하는 ROS 2 Python 런치 파일
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    ROS 2 런치 디스크립션 생성 함수
    """

    # -------------------------------------------------------------------------
    # 1. 외부 입력 런치 인자(Launch Arguments) 선언
    #    - 터미널에서 `ros2 launch ... wheelbase:=2.0` 형태로 동적 재정의 가능
    # -------------------------------------------------------------------------
    wheelbase_arg = DeclareLaunchArgument(
        'wheelbase',
        default_value='1.8',
        description='차량 전륜-후륜 축거(L, m)'
    )

    tread_arg = DeclareLaunchArgument(
        'tread',
        default_value='1.2',
        description='차량 좌우 윤거(W, m)'
    )

    max_steer_arg = DeclareLaunchArgument(
        'max_steering_angle',
        default_value='0.52',
        description='기계적 최대 허용 조향각(rad, 0.52 rad 약 30도)'
    )

    watchdog_timeout_arg = DeclareLaunchArgument(
        'watchdog_timeout',
        default_value='0.5',
        description='통신 단절 판정 워치독 타임아웃 시간(초)'
    )

    control_rate_arg = DeclareLaunchArgument(
        'control_rate',
        default_value='20.0',
        description='제어 루프 실행 주기(Hz)'
    )

    # -------------------------------------------------------------------------
    # 2. 아커만 제어 노드(Ackermann Controller Node) 정의
    # -------------------------------------------------------------------------
    ackermann_controller_node = Node(
        package='my_automotive_pkg',
        executable='ackermann_controller',
        name='ackermann_controller',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'use_sim_time': True,
            'wheelbase': LaunchConfiguration('wheelbase'),
            'tread': LaunchConfiguration('tread'),
            'max_steering_angle': LaunchConfiguration('max_steering_angle'),
            'watchdog_timeout': LaunchConfiguration('watchdog_timeout'),
            'control_rate': LaunchConfiguration('control_rate'),
        }]
    )

    # -------------------------------------------------------------------------
    # 3. 런치 시작 시 콘솔에 상태 안내 메시지 출력
    # -------------------------------------------------------------------------
    start_msg = LogInfo(
        msg='[오토모티브SW프로그래밍 7주차] 아커만 제어 및 안전 워치독 시스템을 시작합니다.'
    )

    # -------------------------------------------------------------------------
    # 4. 전체 런치 요소들을 반환
    # -------------------------------------------------------------------------
    return LaunchDescription([
        wheelbase_arg,
        tread_arg,
        max_steer_arg,
        watchdog_timeout_arg,
        control_rate_arg,
        start_msg,
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('my_automotive_pkg'),
                'launch', 'spawn_car.launch.py'
            ))
        ),
        ackermann_controller_node
    ])
