from flask import Blueprint
from flask_restful import Api
from gm.main.resources import QuantModelMetricsResource, QuantModelMetricResource, \
    MetricsConfigResource, MetricConfigResource, MetricRunsResource, \
    MetricRunResource, MlModelMetricsResource, MlModelMetricResource

# initialize the API blueprints
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Here we associate the Resource subclass, which has the code for handling the HTTP methods
# (GET, PUT, ...), with the an API endpoint.
#
# The endpoints should not have a trailing "/", so that the API is consistent everywhere.
# We could have chosen to add a trailing "/" everywhere, it was a design choice.

# Routes for "quant_model" monitoring
# this dict is required to inject parameters into each Resource subclass, so that inside
# each Resource subclass we know where we are (which base endpoint).
ep_mm_dict = {'service': 'monitoring', 'metric_type': 'quant_model'}
api.add_resource(QuantModelMetricsResource, '/quant_model/metrics',
                 resource_class_kwargs=ep_mm_dict)
api.add_resource(QuantModelMetricResource, '/quant_model/metrics/<int:metric_id>',
                 resource_class_kwargs=ep_mm_dict)
api.add_resource(MetricsConfigResource,
                 '/quant_model/metrics/<int:metric_id>/configs',
                 resource_class_kwargs=ep_mm_dict)
api.add_resource(MetricConfigResource,
                 '/quant_model/metrics/<int:metric_id>/configs/<string:config_name>',
                 resource_class_kwargs=ep_mm_dict)
api.add_resource(MetricRunsResource,
                 '/quant_model/metrics/<int:metric_id>/runs',
                 resource_class_kwargs=ep_mm_dict)
api.add_resource(MetricRunResource,
                 '/quant_model/metrics/<int:metric_id>/runs/<string:run_id>',
                 resource_class_kwargs=ep_mm_dict)

# Routes for "ml_model" monitoring
ep_madm_dict = {'service': 'monitoring', 'metric_type': 'ml_model'}
api.add_resource(MlModelMetricsResource,
                 '/ml_model/metrics',
                 endpoint='ml_model_metrics',
                 resource_class_kwargs=ep_madm_dict)
api.add_resource(MlModelMetricResource,
                 '/ml_model/metrics/<int:metric_id>',
                 endpoint='ml_model_metric',
                 resource_class_kwargs=ep_madm_dict)
api.add_resource(MetricsConfigResource,
                 '/ml_model/metrics/<int:metric_id>/configs',
                 endpoint='ml_model_configs',
                 resource_class_kwargs=ep_madm_dict)
api.add_resource(
    MetricConfigResource,
    '/ml_model/metrics/<int:metric_id>/configs/<string:config_name>',
    endpoint='ml_model_config',
    resource_class_kwargs=ep_madm_dict)
api.add_resource(MetricRunsResource,
                 '/ml_model/metrics/<int:metric_id>/runs',
                 endpoint='ml_model_results',
                 resource_class_kwargs=ep_madm_dict)
api.add_resource(
    MetricRunResource,
    '/ml_model/metrics/<int:metric_id>/results/<string:run_id>',
    endpoint='ml_model_run',
    resource_class_kwargs=ep_madm_dict)
