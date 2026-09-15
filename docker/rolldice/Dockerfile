# The synthetic traffic's target: the rolldice Flask app from the otel-lgtm
# examples, auto-instrumented so that every request becomes a metric the Alert
# rule can watch. Copied from ~/projects/docker-otel-lgtm/examples/python rather
# than built from there, because story 53 keeps that repo read-only and this one
# self-contained.
#
# One departure from the example: a Debian slim base instead of alpine, because
# every dependency has a wheel for it and none has to be compiled during a build
# that might happen an hour before the demo.
#
# What compose sets for it: OTEL_SERVICE_NAME=rolldice, the OTLP endpoint on the
# lgtm service, and a five-second metric export interval so the rate the rule
# reads moves on demo timescales.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# renovate: datasource=pypi depName=opentelemetry-distro
ENV OPENTELEMETRY_DISTRO_VERSION=0.60b0
RUN pip install --no-cache-dir "opentelemetry-distro[otlp]==$OPENTELEMETRY_DISTRO_VERSION" \
    && opentelemetry-bootstrap -a install

COPY app.py .

# Logging support is still in alpha, so we need to enable it explicitly
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_LOGS_EXPORTER=otlp

EXPOSE 8082

CMD ["opentelemetry-instrument", "flask", "run", "--host", "0.0.0.0", "--port", "8082"]
