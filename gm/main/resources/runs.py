from flask import request
from flask_restful import abort
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from gm.main.models.model import db, MetricRun, MetricRunSchema, MetricStatus
from gm.main.resources import success, get_metric_by_id, BaseResource, COB_DATE_FORMAT


def _datestr_to_datetime(date_str, label='cob_date'):
    """
    Function used to convert a date in string to datetime object. If the expected date
    format is not respected the 'abort' function will be called.

    The expected format is defined by the COB_DATE_FORMAT global variable.

    :param date_str: a date in string format
    :param label: the name of the label to parse, used only when raising an error message
    :return: the datetime equivalent of the specified date in string format
    """
    try:
        date_datetime = datetime.strptime(date_str, COB_DATE_FORMAT)
    except ValueError as e:
        abort(400, message=f"Error parsing '{label}' to datetime: {e}")
    return date_datetime


class MetricRunsResource(BaseResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/metrics/{metric_id}/runs".

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, POST
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = MetricRunSchema()
        schema_collection = MetricRunSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)

    def get(self, metric_id):
        """
        Implements the GET method for endpoint "/metrics/{metric_id}/runs". By default
        the results are order by 'cob_date' ascending.

        Implemented Query Parameters:
        - start: to obtain results from this "start" date (including). Format: YYYY-MM-DD.
        - end: to obtain results up to this "end" date (including). Format: YYYY-MM-DD.
        - breach: to filter results that were either in "breach" or not. Case insensitive.
        - status: to filter results according to a given metric result status. Case
        insensitive.
        - sort: allows one to order the resulting collection by 'cob_date' in
        descending order. This should be done by specifying the query parameter as
        "sort=-cob_date". Case insensitive.

        Note: if unknown query parameters are given these will be ignored.

        :param metric_id: the metric_id associated with this endpoint
        :return: a collection of metric results for the specified metric_id
        """
        # base query will always filter by metric_id
        query = MetricRun.query.filter_by(metric_id=metric_id)

        # get query parameters from request
        start = request.args.get('start')
        end = request.args.get('end')
        breach = request.args.get('breach')
        status = request.args.get('status')
        sort = request.args.get("sort")

        # process (convert if needed) each parameter and append to query filters
        if start is not None:
            start = _datestr_to_datetime(start, 'start')
            query = query.filter(MetricRun.cob_date >= start)
        if end is not None:
            end = _datestr_to_datetime(end, 'end')
            query = query.filter(MetricRun.cob_date <= end)
        if breach is not None:
            breach = breach.lower() == 'true'
            query = query.filter_by(breach=breach)
        if status is not None:
            try:
                metric_status = MetricStatus.from_name(status)
            except ValueError as e:
                msg = f"Invalid 'status': {status}. Use one of {MetricStatus.values()}"
                abort(400, message=msg)
            query = query.filter(MetricRun.status == metric_status)
        # check if the 'sort' has been requested for the only implemented field
        if sort is not None and sort.lstrip("-").lower() == 'cob_date':
            query = query.order_by(MetricRun.cob_date.desc())
        else:
            # by default sorts ascending
            query = query.order_by(MetricRun.cob_date)

        # execute query
        results = query.all()

        # dump results into a json like object
        res = self.schema_collection.dump(results)
        return success(result=res)

    def post(self, metric_id):
        """
        Implements the POST method for endpoint "/metrics/{metric_id}/runs". It should
        be used to create a new metric result.

        :param metric_id: the metric_id associated with this endpoint
        :return: the metric result as a json created in the database (in case of success)
        """
        json_data = request.get_json(force=True)
        if not json_data:
            abort(400, 'No input data provided')

        # validate and deserialize input
        new_run = self.load(json_data, session=db.session)

        # get respective metric by the id, associate the newly create result with this
        # metric obtained from the database
        metric = get_metric_by_id(metric_id)
        new_run.metric = metric

        # add object to the database
        try:
            db.session.add(new_run)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        # send result back
        res = self.schema.dump(new_run)
        return success(result=res, code=201)


class MetricRunResource(BaseResource):
    """
    This resource handles the HTTP requests coming to the endpoint
    "/metrics/{metric_id}/runs/<cob_date>".

    The <cob_date> is a string and must follow the format defined in
    gtm.main.common.COB_DATE_FORMAT.

    Note: no trailing slash ("/") should be used.

    Accepted HTTP methods: GET, PUT, DELETE
    """

    def __init__(self, **kwargs):
        """
        Initialize schemas with appropriate classes.

        :param kwargs: pass through to base constructor (service and metric_type)
        """
        schema = MetricRunSchema()
        schema_collection = MetricRunSchema(many=True)
        super().__init__(schema, schema_collection, **kwargs)

    @staticmethod
    def _get_metric_result_by_date(metric_id, cob_date):
        """
        Returns the metric result entity from the database identified by a given metric_id
        and cob_date. The 'abort' method is called if no result is found.

        :param metric_id: the metric_id associated with this endpoint
        :param cob_date: the cob_date being searched.
        :return: the metric result entity retrieved from the database (if found)
        """
        # parse cob_date (string) to datetime
        try:
            cob_datetime = datetime.strptime(cob_date, COB_DATE_FORMAT)
        except ValueError as e:
            abort(400, message=f"Error parsing 'cob_date': {e}")

        # obtain the metric result for the specified metric_id and cob_date
        result = MetricRun.query\
            .filter_by(metric_id=metric_id, cob_date=cob_datetime)\
            .one_or_none()

        # if no metric result exists, raise appropriate error
        if result is None:
            message = f'No Result found for metric_id {metric_id} and cob_date {cob_date}'
            abort(404, message=message)
        return result

    def get(self, metric_id, cob_date):
        """
        Implements the GET method for endpoint "/metrics/{metric_id}/runs/{cob_date}".
        It should be used to get a single metric result from the database.

        :param metric_id: the metric_id associated with this endpoint
        :param cob_date: the cob_date for which the result is being searched
        :return: the json object of metric result found in the database (if it exists)
        """
        result = self._get_metric_result_by_date(metric_id, cob_date)
        return self.schema.jsonify(result)

    def put(self, metric_id, cob_date):
        """
        Implements the PUT method for endpoint "/metrics/{metric_id}/runs/{cob_date}".
        It should be used to update a metric result.

        :param metric_id: the metric_id associated with this endpoint
        :param cob_date: the cob_date for which the result is being updated
        :return: the metric result as a json after the update (in case of success)
        """
        json_data = request.get_json(force=True)
        if not json_data:
            abort(400, message='No input data provided')

        # Validate and deserialize input
        result = self._get_metric_result_by_date(metric_id, cob_date)
        self.load(json_data, instance=result, session=db.session, partial=True)

        # if it was found and deserialized successfully try to commit
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')

        return success(json_data)

    def delete(self, metric_id, cob_date):
        """
        Implements the DELETE method for endpoint
        "/metrics/{metric_id}/runs/{cob_date}". It should be used to delete a metric
        result matching the provided metric_id and cob_date.

        :param metric_id: the metric_id associated with this endpoint
        :param cob_date: the cob_date associated with this endpoint
        :return: the metric result as a json after the delete (in case of success)
        """
        result = self._get_metric_result_by_date(metric_id, cob_date)
        # dump as json to send in the end if del is successful
        res = self.schema.dump(result)

        # if result was found, delete it from database
        try:
            db.session.delete(result)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(400, message=f'Database error. Reason: {e}')
        return success(res)
