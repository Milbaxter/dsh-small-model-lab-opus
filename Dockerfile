FROM python:3.12-slim
RUN pip install --no-cache-dir deepseek-harness-sdk==0.1.5rc1 && useradd -m -u 1000 lab
COPY scripts/actor.py /runner/actor.py
WORKDIR /workspace
USER lab
ENTRYPOINT ["python", "-u", "/runner/actor.py"]
