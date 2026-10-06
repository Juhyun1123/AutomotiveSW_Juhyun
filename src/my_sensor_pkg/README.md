# Sensor vehicle simulation

Vehicle model, track, RViz display and TF examples are copied from
my_vehicle_gazebo. The original package is unchanged. This package is standalone.

In Ubuntu, source your installed ROS 2 distribution, then:

```bash
cd ~/ros2_ws
colcon build --packages-select my_sensor_pkg --symlink-install
source install/setup.bash
ros2 launch my_sensor_pkg spawn_car.launch.py
```

In a second Ubuntu terminal (keep keyboard focus there):

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 run my_sensor_pkg keyboard_teleop
```

Up/down: forward/reverse; left/right: steer while moving; space: stop; Q: quit.
Hold an arrow for key repeat. Release stops after 0.6 seconds; terminal input
does not expose key-up events. Left/right alone cannot turn a stationary
Ackermann car. Simultaneous arrows depend on terminal key-repeat behavior;
press up/down, then hold left/right to drive through a turn.

Default speed is 0.5 m/s, steering angle 0.30 rad, wheelbase 0.40 m.
Override with `--ros-args -p speed:=0.3 -p key_timeout:=0.8`.
Gazebo Sim with gz-sim AckermannSteering, JointStatePublisher, Sensors and Imu
systems and ros_gz packages is required.

Other copied features:

```bash
ros2 launch my_sensor_pkg display.launch.py
ros2 launch my_sensor_pkg tf_demo.launch.py
```

Run TF demo separately from Gazebo to avoid competing odom/base_link TFs.
`sensors_sim.launch.py` remains the bridge/listener-only launch for an already
running simulator. Do not run it alongside spawn_car (duplicate bridges).
Sensors: /scan, /camera/image_raw, /camera/camera_info, /imu/data.
Vehicle: /cmd_vel, /odom, /tf, /joint_states, /clock.

Implementation reference:
https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1AckermannSteering.html
