from flask import request
from flask_restful import abort
from sqlalchemy.exc import SQLAlchemyError

from gm.main.models.model import db, MetricConfig, MetricConfigSchema
from gm.main.resources import success, get_metric_by_id, BaseResource


class MetricsConfigResource(BaseResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/metrics/{metric_id}/configs".

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, POST
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = MetricConfigSchema()
        schema_collection = MetricConfigSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)

    def get(self, metric_id):
        """
        Implements the GET method for endpoint "/metrics/{metric_id}/configs". By default
        the results are order by 'config_name' ascending.

        Implemented Query Parameters:
        - sort: allows one to order the resulting collection by 'config_name' in
        descending order. This should be done by specifying the query parameter as
        "sort=-config_name". Case insensitive.

        Note: if unknown query parameters are given these will be ignored.

        :param metric_id: the metric_id associated with this endpoint
        :return: a collection of metric configs for the specified metric_id
        """
        query = MetricConfig.query.filter_by(metric_id=metric_id)

        # check if the 'sort' has been requested for the only implemented field
        sort = request.args.get("sort")
        if sort is not None and sort.lstrip("-").lower() == 'config_name':
            query = query.order_by(MetricConfig.config_name.desc())
        else:
            # by default sorts ascending
            query = query.order_by(MetricConfig.config_name)

        # execute query
        configs = query.all()

        result = self.schema_collection.dump(configs)
        return success(result=result)

    def post(self, metric_id):
        """
        Implements the POST method for endpoint "/metrics/{metric_id}/configs". It should
        be used to create a new metric config.

        :param metric_id: the metric_id associated with this endpoint
        :return: the metric config as a json created in the database (in case of success)
        """
        json_data = request.get_json(force=True)
        if not json_data:
            abort(400, 'No input data provided')
        # validate and deserialize input
        metric_config = self.load(json_data, session=db.session)

        # get respective metric by the id, associate the newly create config with this
        # metric obtained from the database
        metric = get_metric_by_id(metric_id)
        metric_config.metric = metric

        # add object to db
        try:
            db.session.add(metric_config)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        # send result back
        result = self.schema.dump(metric_config)
        return success(result, code=201)


class MetricConfigResource(BaseResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/metrics/{metric_id}/configs/<config_name>".

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, PUT, DELETE
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = MetricConfigSchema()
        schema_collection = MetricConfigSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)

    def _get_metric_config_by_name(self, metric_id, config_name):
        """
        Returns the metric config entity from the database identified by a given metric_id
        and config_name. The 'abort' method is called if no result is found.

        :param metric_id: the metric_id associated with this endpoint
        :param config_name: the config_name being searched.
        :return: the metric config entity retrieved from the database (if found)
        """
        config = MetricConfig.query\
            .filter_by(metric_id=metric_id, config_name=config_name)\
            .one_or_none()
        if config is None:
            message = 'Metric Config not found for metric_id: {} and config name {}'\
                .format(metric_id, config_name)
            abort(404, message=message)
        return config

    def get(self, metric_id, config_name):
        """
        Implements the GET method for endpoint
        "/metrics/{metric_id}/configs/{config_name}". It should be used to get a single
        metric config from the database.

        :param metric_id: the metric_id associated with this endpoint
        :param config_name: the name of the configuration for which the result is being
        searched
        :return: the json object of metric config found in the database (if it exists)
        """
        config = self._get_metric_config_by_name(metric_id, config_name)
        return self.schema.jsonify(config)

    def put(self, metric_id, config_name):
        """
        Implements the PUT method for endpoint
        "/metrics/{metric_id}/configs/{config_name}". It should be used to update a metric
        config_name.

        :param metric_id: the metric_id associated with this endpoint
        :param config_name: the name of the configuration being updated
        :return: the metric config as a json after the update (in case of success)
        """
        json_data = request.get_json(force=True)
        if not json_data:
            abort(400, message='No input data provided')

        # Validate and deserialize input
        config = self._get_metric_config_by_name(metric_id, config_name)
        self.load(json_data, instance=config, session=db.session, partial=True)

        # if it was found and deserialized successfully try to commit
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        return success(json_data)

    def delete(self, metric_id, config_name):
        """
        Implements the DELETE method for endpoint
        "/metrics/{metric_id}/configs/{config_name}". It should be used to delete a metric
        config matching the provided metric_id and config_name.

        :param metric_id: the metric_id associated with this endpoint
        :param config_name: the name of the configuration being deleted
        :return: the metric config as a json after the delete (in case of success)
        """
        config = self._get_metric_config_by_name(metric_id, config_name)
        result = self.schema.dump(config)

        # if result was found, delete it from database
        try:
            db.session.delete(config)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        return success(result)
