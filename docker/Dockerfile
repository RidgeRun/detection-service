FROM dustynv/mmj:genai_deps-r36.2.0

# Install nano owl
RUN git clone https://github.com/NVIDIA-AI-IOT/nanoowl \
    && cd nanoowl \
    && pip3 install . \
    && echo "Building owl encoder engine" \
    && mkdir data \
    && python3 -m "nanoowl.build_image_encoder_engine" "data/owl_image_encoder_patch32.engine"


# Install mmj_utils
RUN git clone https://github.com/RidgeRun/mmj_utils \
    && cd mmj_utils \
    && pip3 install .

# Copy rrms-utils
COPY rrms-utils /rrms-utils
RUN cd /rrms-utils/ && pip3 install .

# Copy detection
COPY detection /detection
RUN pip3 install --ignore-installed --no-cache-dir blinker \
    && cd /detection && pip3 install --no-cache-dir  .

WORKDIR /detection
RUN gst-inspect-1.0 > /dev/null 2>&1
