# Generic Monitoring REST API Service

This project contains the source code for the Generic Monitoring (GM) API
Service. This API service is implemented as an **HTTP REST API** using **JSON** 
as the payload. The actual implementation is based on the following stack:

- **Python** the programming language used for the REST API implementation.
- **Flask** the web-based framework for building the REST API.
- **Marshmallow** used for marshal/unmarshal of the JSON to Python objects and vice
versa.
- **SqlAlchemy** used for modeling the underlying database tables.
- **Docker** the REST API will be containerized using Docker so that it can be easily
deployed in a remote server.
