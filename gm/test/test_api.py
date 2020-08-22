from gm.main.app import create_app
from flask import json

# build app
app = create_app()


def test_get_quant_model_metrics():
    with app.test_client() as c:
        response = c.get('/api/v1/monitoring/quant_model/metrics')
        assert response.status_code == 200
        body = json.loads(response.data)
        assert body["status"] == "success"
