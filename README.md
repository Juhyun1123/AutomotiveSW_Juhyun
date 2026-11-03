# 9주차 RViz2 심화 시각화 실습

## 실행 방법

ROS 2 Lyrical이 설치된 Ubuntu 터미널에서 실행합니다. 기존 시뮬레이션이 실행 중이면 먼저 종료하고 아래 명령을 한 번만 실행합니다.

```bash
source /opt/ros/lyrical/setup.bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select my_automotive_pkg
source install/setup.bash
ros2 launch my_automotive_pkg rviz_advanced.launch.py
```

차량 모델, LiDAR, 카메라와 경로선·장애물 박스·영문 경고 마커를 함께 표시합니다.

### 마커 자동 소멸 확인

터미널 1에서 마커를 제외한 시뮬레이터와 RViz를 실행합니다.

```bash
source /opt/ros/lyrical/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch my_automotive_pkg rviz_advanced.launch.py start_markers:=false
```

터미널 2에서 마커 노드를 실행합니다.

```bash
source /opt/ros/lyrical/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run my_automotive_pkg custom_marker_publisher --ros-args -p use_sim_time:=true
```

터미널 2에서 Ctrl+C를 누르면 마커만 종료됩니다. 마지막 갱신 후 시뮬레이션 시간 기준 0.2초가 지나면 마커가 자동 소멸합니다.

### 마커 토픽 확인

마커가 실행 중일 때 별도 터미널에서 확인합니다.

```bash
source /opt/ros/lyrical/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 topic echo /visual_markers --once
```

## 실행 화면

![RViz2 실행 화면](img/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7%202026-11-03%20145254.png)

