import enum
import uuid

from marshmallow_enum import EnumField
from marshmallow_sqlalchemy import field_for
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.dialects.postgresql import UUID

# This script is where the our Database Model is defined, the goal is for using this code
# to build the database. Using SQLAlchemy we abstract the way that each database engine
# (Postgres, Oracle, ...) work.
#
# This module is divided in 3 blocks:
# 1. Enum classes - used in model definition
# 2. Model classes - database models with tables, relationships and constraints
# 3. Schema classes - definition of how each model will be serialized/deserialized

# build the Marshmallow object that will allow one create schemas for each of the database
# models
ma = Marshmallow()

# the SQLAlchemy object which has the database models' definitions (code)
db = SQLAlchemy()


##########################################################################################
# 1. Enums
##########################################################################################

class ThresholdType(enum.Enum):
    """
    This enum is used to represent types of thresholds which provide more flexibility
    when defining monitoring metrics.

    Examples:
        GT: metric in breach if metric_value > threshold_value
        LTE: metric in breach if metric_value <= threshold_value
        IN: metric in breach if metric_value in [a, b, c, ...]. The threshold_value is
        defined as multiple values.
    """

    # Greater than or equal. Metric in breach if metric_value >= threshold_value.
    GTE = 1

    # Greater than. Metric in breach if metric_value > threshold_value.
    GT = 2

    # Less than or equal. Metric in breach if metric_value <= threshold_value.
    LTE = 3

    # Less than. Metric in breach if metric_value < threshold_value.
    LT = 4

    # Not equal. Metric in breach if metric_value != threshold_value.
    NE = 5

    # Equal. Metric in breach if metric_value = threshold_value.
    EQ = 6

    # In. Metric in breach if metric_value in [a, b, c, ...]
    IN = 7

    # Not in. Metric in breach if metric_value not in [a, b, c, ...]
    NOT_IN = 8

    # Range. Metric in breach if A <= metric_value <= B
    RANGE = 9

    # Range with Left Open. Metric in breach if A < metric_value <= B
    RANGE_LO = 10

    # Range with Right Open. Metric in breach if A <= metric_value < B
    RANGE_RO = 11

    # Range with Left and Right Open. Metric in breach if A < metric_value < B
    RANGE_LRO = 12

    def is_range(self):
        """
        Returns True if this object is one of the RANGE options (RANGE, RANGE_LO, ...).

        :return: True if this object is one of the RANGE options
        """
        return self.name.startswith("RANGE")

    def is_set(self):
        """
        Returns True if this object is one of the IN/NOT IN options.

        :return: True if this object is one of the IN/NOT IN options.
        """
        return self.name.endswith("IN")

    @classmethod
    def from_name(cls, name):
        # TODO: check if we this method implemented only in one place for all the enums.
        """
        Returns the enum object given an input 'name'. The assessment is case insensitive.

        Use this when you have the enum as a string and you need to convert it to the
        actual enum type. A ValueError is raised if no enum is found for that name.

        :param name: the name of the enum we want to search.
        :return: Returns the enum object given an input 'name'
        """
        for tt in ThresholdType:
            if tt.name == name.upper():
                return tt
        raise ValueError('Invalid name %s' % name)

    @classmethod
    def values(cls):
        """
        Returns this enum's names, useful for displaying on error messages if "the user
        calls the from_name() with a wrong name.

        :return: a list with names of all enum items of this enum type.
        """
        return [e.name for e in ThresholdType]


class ConfigType(enum.Enum):
    """
    This enum is used to represent types of configurations which provide the ability to
    easily obtain the configuration value in the appropriate type and/or after doing some
    processing (e.g.: split a list).
    """

    # the configuration value is a boolean
    BOOLEAN = 1

    # the configuration value is a string
    STRING = 2

    # the configuration value is a float
    FLOAT = 3

    # the configuration value is a list of strings (e.g: a,b,c)
    LIST_STRING = 4

    # the configuration value is a list of floats (e.g: 0.1,0.2,0.3)
    LIST_FLOAT = 5

    # the configuration value is an integer
    INTEGER = 6

    @classmethod
    def from_name(cls, name):
        """
        Returns the enum object given an input 'name'. The assessment is case insensitive.

        Use this when you have the enum as a string and you need to convert it to the
        actual enum type. A ValueError is raised if no enum is found for that name.

        :param name: the name of the enum we want to search.
        :return: Returns the enum object given an input 'name'
        """
        for tt in ConfigType:
            if tt.name == name.upper():
                return tt
        raise ValueError('Invalid name %s' % name)

    @classmethod
    def values(cls):
        """
        Returns this enum's names, useful for displaying on error messages if "the user
        calls the from_name() with a wrong name.

        :return: a list with names of all enum items of this enum type.
        """
        return [e.name for e in ConfigType]


class MetricStatus(enum.Enum):
    """
    This enum is used to represent the status a metric result, i.e., the metric was
    evaluated and if it was processed correctly it should be se as OK. If an error was
    raised during the process the status should be set as FAILED.
    """

    # metric was assessed without any problem and we have a metric_value calculated
    OK = 1

    # metric failed to run due to some error, we don't have a metric_value in this case
    FAILED = 2

    # metric ok, but with warnings (just an idea, probably will not be used)
    WARNING = 3

    # used as a default value when inserting without providing a status
    UNDETERMINED = 4

    @classmethod
    def from_name(cls, name):
        """
        Returns the enum object given an input 'name'. The assessment is case insensitive.

        Use this when you have the enum as a string and you need to convert it to the
        actual enum type. A ValueError is raised if no enum is found for that name.

        :param name: the name of the enum we want to search.
        :return: Returns the enum object given an input 'name'
        """
        for tt in MetricStatus:
            if tt.name == name.upper():
                return tt
        raise ValueError('Invalid name %s' % name)

    @classmethod
    def values(cls):
        """
        Returns this enum's names, useful for displaying on error messages if "the user
        calls the from_name() with a wrong name.

        :return: a list with names of all enum items of this enum type.
        """
        return [e.name for e in MetricStatus]


class Frequency(enum.Enum):
    """
    This enum is used to represent the frequency over which a metric should be executed.
    """

    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    QUARTERLY = 4

    @classmethod
    def from_name(cls, name):
        """
        Returns the enum object given an input 'name'. The assessment is case insensitive.

        Use this when you have the enum as a string and you need to convert it to the
        actual enum type. A ValueError is raised if no enum is found for that name.

        :param name: the name of the enum we want to search.
        :return: Returns the enum object given an input 'name'
        """
        for tt in Frequency:
            if tt.name == name.upper():
                return tt
        raise ValueError('Invalid name %s' % name)

    @classmethod
    def values(cls):
        """
        Returns this enum's names, useful for displaying on error messages if "the user
        calls the from_name() with a wrong name.

        :return: a list with names of all enum items of this enum type.
        """
        return [e.name for e in Frequency]


##########################################################################################
# 2. Model classes
# The order of the class definition matters.
##########################################################################################

class MetricConfig(db.Model):
    """
    This class represents a metric configuration. One metric has 0 or more metric
    configurations. Configurations are identified by 'config_name'.
    """

    # how the table is called in the actual database
    __tablename__ = "metric_config"

    # the primary key is composed of the metric_id and config_name
    metric_id = db.Column(db.Integer, db.Sequence('metric_id_seq'),
                          db.ForeignKey('metric.metric_id'), primary_key=True)
    config_name = db.Column(db.String(50), primary_key=True)

    # the value of the configuration which is stored as a string but can have different
    # types depending on the config_type field
    config_value = db.Column(db.String(255), nullable=False)

    # the type of the config_value and the values are constrained in the database to the
    # values of the ConfigType enum
    config_type = db.Column(db.Enum(ConfigType, name='mc_config_type_check'),
                            default=ConfigType.STRING)

    # definition of the relationship with the Metric entity/model/table
    metric = db.relationship("Metric", back_populates="configs")

    def __repr__(self):
        return f"MetricConfig[{self.metric_id}, {self.config_name}]"


class MetricRun(db.Model):
    """
    This class represents a metric run. One metric has 0 or more runs. A run is the
    evaluation of the actual metric. Runs are indexed by run_id.

    Some fields have been set with default values to enable the insertion of new entities
    without a value (and without that value being null).
    """

    # how the table is called in the actual database
    __tablename__ = "metric_run"

    # the primary key is the run_id
    run_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    metric_id = db.Column(db.Integer, db.Sequence('metric_id_seq'),
                          db.ForeignKey('metric.metric_id'))

    # the type of threshold value, which is stored as a string
    # the database column is restricted to the values contained in the ThresholdType
    # enum
    threshold_type = db.Column(db.Enum(ThresholdType, name='mh_threshold_type_check'),
                               default=ThresholdType.GT)
    threshold_value = db.Column(db.String(50), default="0")

    # where the actual result is stored
    metric_value = db.Column(db.String(60), nullable=False)

    # boolean indicating whether the threshold assessment result in breach or not
    breach = db.Column(db.Boolean)

    # the execution time of the metric that generated this result
    exec_time = db.Column(db.DateTime)

    # the status of the metric execution which
    status = db.Column(db.Enum(MetricStatus, name='mh_status_check'),
                       default=MetricStatus.UNDETERMINED)

    # a field for storing messages after the metric execution (e.g.: with information
    # about an error that might have happened when running the metric code)
    message = db.Column(db.String(100))

    # definition of the relationship with the Metric entity/model/table
    metric = db.relationship("Metric", back_populates="runs")

    def __repr__(self):
        return f"MetricRun[{self.run_id}, {self.metric_id}]"


class Metric(db.Model):
    """
    This class represents a metric, which is linked to a monitoring that one wants to
    run with a given frequency. This monitoring metric is tied to a specific monitoring
    type, which is identified as 'metric_type'. One example being metric_type = 'model',
    for which we have "model metrics" (which is a type of report).

    A metric has 0 or more metric configurations and 0 or more metric runs. The
    metric configurations are properties (configurations) that provide information on how
    the monitoring should be executed.

    The history of the metric runs is stored in the metric run entity.

    This entity is the base class of all types of metrics (which are differentiated by
    the metric_type field) and will contain all the fields (and relationships) that are
    common to all types of metrics. The fields that are specific to each type of
    monitoring are stored in subclasses (e.g.: 'model_name' is specific to a Quant Model
    metric). Each subclass will have a separate table in the underlying database.

    Some fields have been set with default values to enable the insertion of new entities
    without a value (and without that value being null).
    """

    # how the table is called in the actual database
    __tablename__ = "metric"

    # metric_id is the primary key
    metric_id = db.Column(db.Integer, db.Sequence('metric_id_seq'), primary_key=True)

    # metric_type is used to different the types of monitoring metrics
    metric_type = db.Column(db.String(50), nullable=False)

    # a user friendly description that explains what this metric is assessing
    description = db.Column(db.String(1000))

    # the type of threshold value, which is stored as a string
    # the database column is restricted to the values contained in the ThresholdType
    # enum.
    # These fields can change over time
    threshold_type = db.Column(db.Enum(ThresholdType, name='m_threshold_type_check'),
                               default=ThresholdType.GT)
    threshold_value = db.Column(db.String(50), default="")

    # a boolean indicating whether the metric is active (should be considered) in official
    # reports
    is_active = db.Column(db.Boolean, default=False)

    # the frequency with which this metric should be executed
    frequency = db.Column(db.Enum(Frequency, name='m_frequency_check'),
                          default=Frequency.WEEKLY)

    # the results field is a collection of 0 or more metric result entities
    # the cascade option is configured to delete the results associated with this metric
    # when the metric is deleted
    runs = db.relationship("MetricRun", back_populates="metric",
                           cascade="all, delete-orphan")

    # the configs field is a collection of 0 or more metric config entities
    # the cascade option is configured to delete the configs associated with this metric
    # when the metric is deleted
    configs = db.relationship("MetricConfig", back_populates="metric",
                              cascade="all, delete-orphan")

    # this configuration is necessary because the Metric entity will be extended by other
    # entities (e.g.: ModelMetric). Hence, we need to identify that the base class/table
    # will be the metric and that the field used to distinguish the various subtypes will
    # be the 'metric_type'. For each different type
    __mapper_args__ = {
        "polymorphic_identity": "metric",
        "polymorphic_on": metric_type,
    }

    def __repr__(self):
        return f"Metric[{self.metric_id}]"


class QuantModelMetric(Metric):
    """
    This class represents a Quant Model metric and is an extension of the base Metric
    entity. It serves to add fields that are specific to the quant model monitoring.

    The table for this entity will only contain the fields that are specific to this
    entity (the only common field will be the metric_id).
    """

    # how the table is called in the actual database
    __tablename__ = "quant_model_metric"

    # the primary key and it's also a foreign key to the metric_id of the base metric
    # table
    metric_id = db.Column(db.Integer, db.Sequence('metric_id_seq'),
                          db.ForeignKey('metric.metric_id'), primary_key=True)

    # the (instrument) model associated with this metric
    model_name = db.Column(db.String(100))

    # the asset class (equities, credit, ...) associated with this metric
    asset_class = db.Column(db.String(20))

    # the pricing library where the model associated with this metric is implemented
    pricing_library = db.Column(db.String(20))

    # a boolean indicating whether the metric is active (should be considered) in official
    # reports
    triggers_regulatory_notification = db.Column(db.Boolean, default=False)

    # this configuration links this entity/table to the metric by saying that metrics
    # that have metric_type = 'model' are associated with this entity
    __mapper_args__ = {"polymorphic_identity": "quant_model"}

    def __repr__(self):
        return f'{super().__repr__()} model {self.model_name}'


class MlModelMetric(Metric):
    """
    This class represents a ML Model metric and is an extension of the base Metric entity. 
    It serves to add fields that are specific to this monitoring.

    The table for this entity will only contain the fields that are specific to this
    entity (the only common field will be the metric_id).
    """

    # how the table is called in the actual database
    __tablename__ = "ml_model_metric"

    # the primary key and it's also a foreign key to the metric_id of the base metric
    # table
    metric_id = db.Column(db.Integer, db.Sequence('metric_id_seq'),
                          db.ForeignKey('metric.metric_id'), primary_key=True)

    # the MRX RiskType associated with this metric
    category = db.Column(db.String(40))

    # the name of this risk measure in GPrime
    sub_category = db.Column(db.String(30))

    # the name of this risk measure in Nexus
    algorithm = db.Column(db.String(60))

    # this configuration links this entity/table to the metric by saying that metrics
    # that have metric_type = 'ml_model_metric' are associated with this entity
    __mapper_args__ = {"polymorphic_identity": "ml_model_metric"}

    def __repr__(self):
        return f'{super().__repr__()} algorithm {self.algorithm}'


##########################################################################################
# 2. Schema classes
# The schema classes associated with each Model class and that define how the each object
# should be marshall/unmarshalled
##########################################################################################

class MetricConfigSchema(ma.SQLAlchemyAutoSchema):
    """
    The schema associated with MetricConfig entity, this is specified in the Meta
    inner class.

    The fields defined below are needed for special types like enums, relationships or
    for indicating that some field should be excluded.
    """

    # required as it's an enum and we want the enum name (by default it's the value)
    config_type = EnumField(ConfigType, by_name=True)

    # metric_id is only used when dumping the object to json
    metric_id = field_for(MetricConfig, 'metric_id', dump_only=True)

    class Meta:
        model = MetricConfig
        load_instance = True


class MetricRunSchema(ma.SQLAlchemyAutoSchema):
    """
    The schema associated with MetricResult entity, this is specified in the Meta inner
    class.

    The fields defined below are needed for special types like enums, relationships or
    for indicating that some field should be excluded.
    """

    # required as it's an enum and we want the enum name (by default it's the value)
    threshold_type = EnumField(ThresholdType, by_name=True)

    # required as it's an enum and we want the enum name (by default it's the value)
    status = EnumField(MetricStatus, by_name=True)

    # metric_id is only used when dumping the object to json
    metric_id = field_for(MetricRun, 'metric_id', dump_only=True)

    class Meta:
        model = MetricRun
        load_instance = True


class MetricSchema(ma.SQLAlchemyAutoSchema):
    """
    The schema associated with Metric entity, this is specified in the Meta inner
    class.

    The fields defined below are needed for special types like enums, relationships or
    for indicating that some field should be excluded.
    """

    # required as it's an enum and we want the enum name (by default it's the value)
    threshold_type = EnumField(ThresholdType, by_name=True)

    # required as it's an enum and we want the enum name (by default it's the value)
    frequency = EnumField(Frequency, by_name=True)

    # metric_id is only used when dumping the object to json
    metric_id = field_for(Metric, 'metric_id', dump_only=True)

    # definition of how the configs and results collections will be shown when
    # dumping the object into a json-like structure. The below config says that we
    # have a many relationship (it's a collection) and the Pluck class will flatten
    # the results so that only the field identified as 'field_name' will be shown.
    # Below in the commented line an option is shown for the configuration that one
    # could have used in alternative, where the full object of the collection would
    # be shown.
    configs = ma.Pluck(MetricConfigSchema, field_name='config_name', many=True)
    runs = ma.Pluck(MetricRunSchema, field_name='run_id', many=True)

    class Meta:
        model = Metric
        load_instance = True


class QuantModelMetricSchema(MetricSchema):
    """
    The schema associated with ModelMetric entity, this is specified in the Meta inner
    class.

    The fields defined below are needed for special types like enums, relationships or
    for indicating that some field should be excluded.
    """

    # metric_id is only used when dumping the object to json
    metric_id = field_for(QuantModelMetric, 'metric_id')

    class Meta(MetricSchema.Meta):
        model = QuantModelMetric
        load_instance = True


class MlModelMetricSchema(MetricSchema):
    """
    The schema associated with MadTransformationMetric entity, this is specified in the
    Meta inner class.

    The fields defined below are needed for special types like enums, relationships or
    for indicating that some field should be excluded.
    """

    # metric_id is only used when dumping the object to json
    metric_id = field_for(MlModelMetric, 'metric_id')

    class Meta(MetricSchema.Meta):
        model = MlModelMetric
        load_instance = True
