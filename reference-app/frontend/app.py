from flask import Flask, render_template, request
from os import getenv
from jaeger_client import Config
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory
from prometheus_flask_exporter import PrometheusMetrics


app = Flask(__name__)

metrics = PrometheusMetrics(app, group_by='endpoint')

# static information as metric
metrics.info('app_info', 'Application info', version='1.0.3')
metrics.register_default(
    metrics.counter(
        'by_path_counter', 'Request count by request endpoint',
        labels={'endpoint': lambda: request.endpoint}
    )
)

endpoint_counter = metrics.counter(
    'endpoint_counter', 'Request count by request endpoint',
    labels={'endpoint': lambda: request.endpoint}
)
JAEGER_AGENT_HOST = getenv('JAEGER_AGENT_HOST', 'localhost')

def init_tracer(service):
    config = Config(
            {'sampler': {'type': 'const', 'param': 1},
                                'logging': True,
                                'local_agent':
                                # Also, provide a hostname of Jaeger instance to send traces to.
                                {'reporting_host': JAEGER_AGENT_HOST}},
            service_name=service,
            validate=True,
            metrics_factory=PrometheusMetricsFactory(service_name_label=service),
    )
    tracer = config.initialize_tracer()
    # this call also sets opentracing.tracer
    return tracer



tracer = init_tracer('frontend')

@app.route("/")
@endpoint_counter
def homepage():
    return render_template("main.html")


if __name__ == "__main__":
    app.run()
