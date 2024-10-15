# Use the base image you specified
FROM elandini84/google_cloud_cpp:v2.22_yarp_ubuntu_22_04_master

ENV DEBIAN_FRONTEND="noninteractive"

# Install necessary packages
USER root

RUN git clone https://github.com/elandini84/libfvad && \
    cd libfvad && \
    autoreconf -i && \
    ./configure && \
    make install

RUN git clone https://github.com/hsp-iit/tour-guide-robot && \
    cd tour-guide-robot && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j4

ENV PATH=$PATH:/usr/local/src/robot/tour-guide-robot/build/bin

RUN pip install openai

# Set the working directory
WORKDIR /workdir/

COPY code /workdir/code
 
# Your entrypoint or CMD here
CMD ["/bin/bash -c"]

