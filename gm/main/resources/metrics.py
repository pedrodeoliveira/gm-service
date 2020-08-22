from flask import request
from flask_restful import abort
from sqlalchemy.exc import SQLAlchemyError

from gm.main.models.model import db, Metric, QuantModelMetricSchema, \
    MlModelMetricSchema, Frequency, QuantModelMetric, MlModelMetric, \
    ThresholdType
from gm.main.resources import success, get_metric_by_id, BaseResource


class MetricsResource(BaseResource):
    """
    This resource handles the HTTP requests coming to the endpoint "/metrics".

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, POST
    """

    def get(self):
        """
        Implements the GET method for endpoint "/metrics". By default the results are
        order by 'metric_id' ascending.

        Implemented Query Parameters:
        - is_active: to filter results that are either active or inactive. Boolean and
        case insensitive.
        - frequency: filter results based on a metric frequency. Values of this enum must
        be respected. Case insensitive.
        - threshold_type: filter results based on a metric threshold type. Values of this
        enum must be respected. Case insensitive.
        - sort: allows one to order the resulting collecting by 'metric_id' in descending
        order. This should be done by specifying the query parameter as "sort=-metric_id".
        Case insensitive.

        Note: if unknown query parameters are given these will be ignored.

        :return: a collection of metrics
        """
        query = self.build_query()
        metrics = query.all()
        result = self.schema_collection.dump(metrics)
        return success(result)

    def build_query(self):
        """
        Builds the query (without executing it) to the be used in the GET method.
        :return: query with all the query conditions specified for obtaining the metrics
        that are in the database and respect the desired filters (query parameters).
        """

        # this filter is required
        query = Metric.query.filter(Metric.metric_type == self.metric_type)

        # get query parameters (parameters which are not here are ignored)
        is_active = request.args.get('is_active')
        frequency = request.args.get('frequency')
        threshold_type = request.args.get('threshold_type')
        sort = request.args.get('sort')

        # process each parameter, and if valid add it as a query condition
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            query = Metric.query.filter_by(is_active=is_active)
        if frequency is not None:
            try:
                frequency = Frequency.from_name(frequency)
            except ValueError as e:
                msg = f"Invalid 'frequency': {frequency}. Use one of {Frequency.values()}"
                abort(400, message=msg)
            query = query.filter_by(frequency=frequency)
        if threshold_type is not None:
            try:
                threshold_type = ThresholdType.from_name(threshold_type)
            except ValueError as e:
                msg = f"Invalid 'threshold_type': {threshold_type}. Use one of " \
                      f"{ThresholdType.values()}"
                abort(400, message=msg)
            query = query.filter_by(threshold_type=threshold_type)
        if sort is not None and sort.lstrip("-") == 'metric_id':
            query = query.order_by(Metric.metric_id.desc())
        else:
            query = query.order_by(Metric.metric_id)

        return query


    def post(self):
        """
        Implements the POST method for endpoint "/metrics". It should be used to create a
        new metric.

        :return: the metric as a json created in the database (in case of success)
        """
        json_data = request.get_json(force=True)
        if not json_data:
            abort(400, message='No input data provided')
        # make sure the metric_id (temporary) and metric_type (model) are filled
        json_data["metric_id"] = "TBD"
        json_data["metric_type"] = "model"

        # validate and deserialize input
        new_metric = self.load(json_data, session=db.session)

        # get the next metric id and update metric object
        try:
            db.session.add(new_metric)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        # dump to json and return result
        result = self.schema.dump(new_metric)
        return success(result, code=201)


class QuantModelMetricsResource(MetricsResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/quant_model/metrics/{metric_id}".

    This subclass uses almost everything from the base class, it only needs to specify the
    appropriate schemas in the constructor, and to override the build_query method so that
    the appropriate metric_type is filtered and the remaining query parameters (specific
    to this endpoint) are processed.

    Implemented Query Parameters:
    - asset_class: to filter results by a given asset class.
    - model_name: to filter results by a given model name.
    - pricing_library: to filter results for a given pricing library.

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, POST
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = QuantModelMetricSchema()
        schema_collection = QuantModelMetricSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)

    def build_query(self):
        """
        Override method to include specific query parameters to this model endpoint.
        """
        # build query from base class add required field for joining with parent
        query = super().build_query()
        query = query.filter(Metric.metric_id == QuantModelMetric.metric_id)

        # get the remaining query parameters
        asset_class = request.args.get('asset_class')
        model_name = request.args.get('model_name')
        pricing_library = request.args.get('pricing_library')

        # process each parameter and, if valid, add as a query condition
        if asset_class is not None:
            query = query.filter(QuantModelMetric.asset_class == asset_class)
        if model_name is not None:
            query = query.filter(QuantModelMetric.model_name == model_name)
        if pricing_library is not None:
            query = query.filter(QuantModelMetric.pricing_library == pricing_library)
        return query


class MlModelMetricsResource(MetricsResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/ml_model/metrics/{metric_id}".

    This subclass uses almost everything from the base class, it only needs to specify the
    appropriate schemas in the constructor, and to override the build_query method so that
    the appropriate metric_type is filtered and the remaining query parameters (specific
    to this endpoint) are processed.

    Implemented Query Parameters:
    - algorithm: to filter results by a given algorithm.

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, POST
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = MlModelMetricSchema()
        schema_collection = MlModelMetricSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)

    def build_query(self):
        """
        Override method to include specific query parameters to this ml_model
        endpoint.
        """
        query = super().build_query()
        query = query.filter(Metric.metric_id == MlModelMetric.metric_id)
        algorithm = request.args.get('algorithm')
        if algorithm is not None:
            query = query.filter(MlModelMetric.algorithm == algorithm)
        return query


class MetricResource(BaseResource):
    """
    This resource handles the HTTP requests coming to the endpoint "/metrics/{metric_id}".

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, PUT, DELETE
    """

    def get(self, metric_id):
        """
        Implements the GET method for endpoint "/metrics/{metric_id}". It should be used
        to get a single metric from the database.

        :param metric_id: the metric_id associated with this endpoint
        :return: the json object of metric found in the database (if it exists)
        """
        metric = get_metric_by_id(metric_id)
        return self.schema.jsonify(metric)

    def put(self, metric_id):
        """
        Implements the PUT method for endpoint "/metrics/{metric_id}". It should be used
        to update a metric.

        :param metric_id: the metric_id associated with this endpoint
        :return: the metric as a json after the update (in case of success)
        """
        json_data = request.get_json(force=True)
        if not json_data:
            abort(400, message='No input data provided')

        # Validate and deserialize input
        metric = get_metric_by_id(metric_id)
        self.load(json_data, metric, db.session, partial=True)

        # if it was found and deserialized successfully try to commit
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        return success(json_data)

    def delete(self, metric_id):
        """
        Implements the DELETE method for endpoint "/metrics/{metric_id}". It should be
        used to delete a metric result matching the provided metric_id and cob_date.

        :param metric_id: the metric_id associated with this endpoint
        :return: the metric as a json after the delete (in case of success)
        """
        metric = get_metric_by_id(metric_id)
        # dump as json to send in the end if del is successful
        result = self.schema.dump(metric)

        # if result was found, delete it from database
        try:
            db.session.delete(metric)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')
        return success(result)


class QuantModelMetricResource(MetricResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/quant_model/metrics/{metric_id}".

    This subclass uses everything from the base class and only needs to specify the
    appropriate schemas in the constructor.

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, PUT, DELETE
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = QuantModelMetricSchema()
        schema_collection = QuantModelMetricSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)


class MlModelMetricResource(MetricResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/ml_model/metrics/{metric_id}".

    This subclass uses everything from the base class and only needs to specify the
    appropriate schemas in the constructor.

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, PUT, DELETE
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = MlModelMetricSchema()
        schema_collection = MlModelMetricSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)