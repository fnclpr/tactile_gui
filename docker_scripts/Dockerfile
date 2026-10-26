FROM osrf/ros:jazzy-desktop

#Uncomment the following line if you get the "release file is not valid yet" error during apt-get
#	(solution from: https://stackoverflow.com/questions/63526272/release-file-is-not-valid-yet-docker)
#RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" | cat > /etc/apt/apt.conf.d/10no--check-valid-until

#Install essential
RUN apt-get update && apt-get install -y

#Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0
ENV HOME=/home/user
ENV ROS_DISTRO=jazzy

# Rimuove l'utente/gruppo predefinito 'ubuntu' presente nelle immagini base di Ubuntu 24.04
RUN if id -u ubuntu >/dev/null 2>&1; then userdel -f -r ubuntu || true; fi && \
    if getent group ubuntu >/dev/null 2>&1; then groupdel ubuntu || true; fi

#Add non root user using UID and GID passed as argument
ARG USER_ID
ARG GROUP_ID
RUN addgroup --gid $GROUP_ID user
RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user
# Aggiunta permessi per la gestione di porte seriali USB e dispositivi
RUN usermod -aG dialout,tty,plugdev user
RUN echo "user:user" | chpasswd
RUN echo "user ALL=(ALL:ALL) ALL" >> /etc/sudoers
USER user

# Install essential system dependencies, PyQt6, PyQtGraph and serial utility
USER root
RUN apt-get update && apt-get install -y \
    python3-pyqt6 \
    python3-pyqtgraph \
    python3-numpy \
    python3-opengl \
    python3-matplotlib \
    setserial \
    ros-jazzy-xacro \
    && rm -rf /var/lib/apt/lists/*
USER user

# ROS2 workspace creation and compilation
RUN mkdir -p ${HOME}/ros2_ws/src
WORKDIR ${HOME}/ros2_ws/
#COPY --chown=user ./src ${HOME}/ros2_ws/src
RUN rosdep update
USER root
RUN rosdep install -i --from-paths src --rosdistro ${ROS_DISTRO} -y 
USER user
SHELL ["/bin/bash", "-c"] 
RUN source /opt/ros/${ROS_DISTRO}/setup.bash; colcon build --symlink-install

# Add script and export env variables to .bashrc
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash;" >>  ${HOME}/.bashrc
RUN echo "source ${HOME}/ros2_ws/install/local_setup.bash;" >>  ${HOME}/.bashrc
RUN echo "source /usr/share/colcon_cd/function/colcon_cd.sh" >> ${HOME}/.bashrc
RUN echo "export _colcon_cd_root=/opt/ros/${ROS_DISTRO}/" >> ${HOME}/.bashrc
RUN echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> ${HOME}/.bashrc
RUN echo "export GAZEBO_AUDIO=0" >> ${HOME}/.bashrc
RUN echo "export GZ_SIM_RESOURCE_PATH=~/ros2_ws/src/ros2_iiwa/iiwa_description/gazebo/models" >> ${HOME}/.bashrc

# USER root
# RUN apt-get upgrade -y && apt-get update -y
# RUN apt-get install ros-jazzy-xacro
# USER user

# Clean image
USER root
RUN rm -rf /var/lib/apt/lists/*
#RUN chown root:user /dev/video0
USER user
