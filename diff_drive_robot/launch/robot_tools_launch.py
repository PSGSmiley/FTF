#!/usr/bin/env python

# Copyright 1996-2023 Cyberbotics Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Launch additional tools for e-puck controller to allow visualization, mapping and navigation."""

import os
import launch
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory, get_packages_with_prefixes
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    launch_description_nodes = []
    package_dir = get_package_share_directory('diff_drive_robot')
    slam_params_file = os.path.join(package_dir, 'config', 'slam_config.yaml')
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)
    use_nav = LaunchConfiguration('nav', default=False)
    use_slam = LaunchConfiguration('slam', default=False)
    use_rviz = LaunchConfiguration('rviz', default=False)
    use_rtabmap = LaunchConfiguration('rtabmap', default=False)
    rtabmap_localization = LaunchConfiguration('localization', default=False)
    use_cartographer = LaunchConfiguration('cartographer', default=False)


    # Rviz node
    rviz_config = os.path.join(package_dir, 'config', 'rviz2.rviz')
    launch_description_nodes.append(
        Node(
            package='rviz2',
            executable='rviz2',
            output='log',
            arguments=['--display-config=' + rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=launch.conditions.IfCondition(use_rviz)
        )
    )
    # SLAM_Toolbox
    launch_description_nodes.append(
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            parameters=[slam_params_file, {'use_sim_time': use_sim_time}],
            remappings=[
                ('odom', '/odom'),
                ('scan', '/scan'),
            ],
            output='log',
            condition=launch.conditions.IfCondition(use_slam),
        )
    )
    # RTABMAP #todo
    launch_description_nodes.append(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(package_dir, 'launch', 'robot_rtabmap_launch.py')
            ),
            launch_arguments={
                'localization': rtabmap_localization,
                'use_sim_time': use_sim_time,
            }.items(),
            condition=launch.conditions.IfCondition(use_rtabmap)
        )
    )
    # Cartographer
    launch_description_nodes.append(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(package_dir, 'launch', 'cartographer_launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
            }.items(),
            condition=launch.conditions.IfCondition(use_cartographer)
        )
    )
    # Navigation
    if 'nav2_bringup' in get_packages_with_prefixes():
        launch_description_nodes.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')
                ),
                launch_arguments=[
                    ('params_file', os.path.join(package_dir, 'config', 'nav2_params.yaml'))
                ],
                condition=launch.conditions.IfCondition(use_nav)
            )
        )
    else:
        launch_description_nodes.append(LogInfo(msg='Navigation2 is not installed, navigation functionality is disabled'))

    # Launch descriptor
    return LaunchDescription(launch_description_nodes)