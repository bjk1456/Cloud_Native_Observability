from flask import Flask, render_template, request, jsonify
from os import getenv
from jaeger_client import Config
import pymongo
from flask_pymongo import PyMongo
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory


app = Flask(__name__)

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)
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



tracer = init_tracer('backend')


@app.route("/")
def homepage(): 
    return "Hello World"


@app.route("/api")
def my_api():
    with tracer.start_span('/api') as span:
        answer = "something"
        span.set_tag('api', answer)
        return jsonify(repsonse=answer)


@app.route("/star", methods=["POST"])
def add_star():
    with tracer.start_span('/star') as span:
        star = mongo.db.stars
        name = request.json["name"]
        distance = request.json["distance"]
        star_id = star.insert({"name": name, "distance": distance})
        new_star = star.find_one({"_id": star_id})
        output = {"name": new_star["name"], "distance": new_star["distance"]}
        span.set_tag('star', output)
        return jsonify({"result": output})



if __name__ == "__main__":
    app.run()
