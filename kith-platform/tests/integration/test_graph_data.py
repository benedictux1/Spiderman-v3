import json


def login(client, username, password):
    return client.post('/api/auth/login', 
                      data=json.dumps({'username': username, 'password': password}),
                      content_type='application/json',
                      follow_redirects=True)


class TestGraphData:
    def test_new_contact_appears_in_graph_nodes(self, client, db_session, sample_user):
        login(client, sample_user.username, "test_password")

        # 1) Create a new contact via API
        contact_name = 'Graph Test Contact'
        resp = client.post('/api/contacts', 
                           data=json.dumps({'full_name': contact_name, 'tier': 2}),
                           content_type='application/json')
        assert resp.status_code in (200, 201)

        # 2) Fetch graph data and assert the contact is included among nodes
        g = client.get('/api/graph-data')
        assert g.status_code == 200
        data = g.get_json()
        assert 'nodes' in data
        labels = [n.get('label') for n in data['nodes']]
        assert contact_name in labels



