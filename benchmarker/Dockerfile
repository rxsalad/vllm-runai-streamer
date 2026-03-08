# https://hub.docker.com/r/rocm/vllm/tags
FROM docker.io/vllm/vllm-openai-rocm:v0.15.1

# Install essential utilities
RUN apt-get update && apt-get install -y curl net-tools iputils-ping nano tree

# Optional: Install VS Code Server
RUN curl -Lk 'https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64' -o vscode_cli.tar.gz && \
    tar -xf vscode_cli.tar.gz && \
    mv code /usr/local/bin/code && \
    rm vscode_cli.tar.gz

# To connect using VS Code:
# Log in the instance using the terminal, and then run the following commands:
# code tunnel user login --provider github
# nohup code tunnel --accept-server-license-terms --name 001 &> output.log &

# Install rclone and prepare config directory
# https://rclone.org/downloads/
RUN curl -Lk 'https://downloads.rclone.org/v1.73.1/rclone-v1.73.1-linux-amd64.deb' -o rclone-v1.73.1-linux-amd64.deb && \
    dpkg -i rclone-v1.73.1-linux-amd64.deb && \
    rm rclone-v1.73.1-linux-amd64.deb 

RUN pip install --upgrade pip
RUN pip install python-dotenv pymongo 

WORKDIR /app

COPY benchmark.py helper.py /app/

CMD ["python3", "benchmark.py"]
# Image: docker.io/richardxgf/amd:vllm_0.11.1
# https://hub.docker.com/repository/docker/richardxgf/amd/tags


# docker image build -t docker.io/richardxgf/vllm:model_streamer_benchmarker_1.0 -f Dockerfile .
# docker push docker.io/richardxgf/vllm:model_streamer_benchmarker_1.0