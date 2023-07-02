FROM ghcr.io/mmesek/mframework:main as base

COPY requirements.txt ./
RUN python -m pip --disable-pip-version-check --no-cache-dir install -r requirements.txt \
    && rm -rf requirements.txt
