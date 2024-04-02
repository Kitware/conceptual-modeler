FROM kitware/trame:py3.10-glvnd

# Copy the server directory
COPY --chown=trame-user:trame-user . /local-app
COPY --chown=trame-user:trame-user .deploy /deploy

RUN /opt/trame/entrypoint.sh build