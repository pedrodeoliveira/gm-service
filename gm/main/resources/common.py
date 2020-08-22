from gm.main.models.model import Metric
from flask_restful import abort, Resource
from marshmallow.exceptions import ValidationError

# the cob_date format that must be used to convert between datetime to str and vice-versa
COB_DATE_FORMAT = '%Y-%m-%d'


def success(result, code=200):
    """
    This function builds the json-like object to be returned as a success message. By
    default the HTTP response status code should be 200 (in some cases 201).

    :param result: the data of the response message
    :param code: the HTTP response status code
    :return: tuple with json object with response data and status code
    """
    return {"status": "success", "data": result}, code


def get_metric_by_id(metric_id):
    """
    Returns the Metric entity found in the database given a metric_id. The 'abort'
    function will be called if the metric is not found.

    :param metric_id: metric_id to search for
    :return: the Metric entity found for provided metric id (if it exists)
    """
    metric = Metric.query.filter_by(metric_id=metric_id).one_or_none()
    if metric is None:
        abort(404, message='Metric not found for Id: {}'.format(metric_id))
    return metric


class BaseResource(Resource):
    """
    This class represents the base Resource of every Resource defined in the API. It
    extends the flask_restful.Resource by providing a constructor that initializes
    the necessary schemas.

    It also provides functions common to all Resources, like the 'load' function.
    """

    def __init__(self, schema, schema_collection, **kwargs):
        """
        Initializes this Resource with the schema of the respective entity and entity
        in collection-mode (e.g: schema for one Metric and schema for a collection of
        Metrics). Other variables allow the code running inside a Resource to know
        which base endpoint it refers (which service and metric_type it belongs).

        :param schema: schema for one entity
        :param schema_collection: schema for a collection of entities
        :param kwargs: service and metric_type provided
        """
        self.schema = schema
        self.schema_collection = schema_collection
        self.service = kwargs['service']
        self.metric_type = kwargs['metric_type']

    def load(self, data, instance=None, session=None, partial=False):
        """
        Common load function for all Resources, it essentially provides an handle of
        the exception by calling the 'abort' function with the appropriate message and
        error code.

        :param data: the json data to load into an object instance
        :param instance: the instance of model entity to load
        :param session: the database session
        :param partial: whether the load should be partial or not, if not every required
        field will be checked and an exception is raised if required fields are missing.
        :return:
        """
        try:
            return self.schema.load(data, instance=instance, session=session,
                                    partial=partial)
        except ValidationError as e:
            abort(400, message=e.messages)
