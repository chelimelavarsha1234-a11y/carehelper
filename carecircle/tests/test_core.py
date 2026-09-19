import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models.request import HelpRequest
from models.user import User


def test_homepage_has_module_sections_and_register():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Elderly Support' in html
    assert 'Family Portal' in html
    assert 'Care Helper' in html
    assert 'Admin Portal' in html
    assert 'Register' in html
    assert '/elderly/login' in html
    assert '/family/login' in html
    assert '/helper/login' in html
    assert '/admin/login' in html


def test_role_login_routes_exist():
    client = app.test_client()
    for path in ['/elderly/login', '/family/login', '/helper/login', '/admin/login']:
        response = client.get(path)
        assert response.status_code == 200


def test_family_arrange_care_requires_login():
    client = app.test_client()
    response = client.get('/family/arrange-care')
    assert response.status_code == 302


def test_helper_dashboard_shows_requester_details():
    client = app.test_client()
    with app.app_context():
        elderly = User.query.filter_by(email='lakshmi@carecircle.com').first()
        if not elderly:
            raise AssertionError('Seed elderly user not found')

        help_request = HelpRequest(
            elderly_id=elderly.id,
            created_by=elderly.id,
            category='Grocery Assistance',
            description='Needs groceries and a short walk to the pharmacy.',
            location='Hyderabad',
            date='Today',
            time='ASAP',
            status='open'
        )
        db.session.add(help_request)
        db.session.commit()

    login = client.post('/helper/login', data={'email': 'anitha@carecircle.com', 'password': 'anitha123'}, follow_redirects=False)
    assert login.status_code == 302

    response = client.get('/helper/dashboard')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Lakshmi Rao' in html
    assert 'Grocery Assistance' in html


def test_registration_type_routes_exist():
    client = app.test_client()
    for path in ['/register', '/register/elderly', '/register/family', '/register/helper']:
        response = client.get(path)
        assert response.status_code == 200


def test_helper_dashboard_redirect_and_request_lifecycle():
    client = app.test_client()
    with app.app_context():
        elderly = User.query.filter_by(email='lakshmi@carecircle.com').first()
        helper = User.query.filter_by(email='sindhu@gmail.com').first()
        helper_id = helper.id
        help_request = HelpRequest(
            elderly_id=elderly.id,
            created_by=elderly.id,
            category='Grocery Assistance',
            description='Please help with groceries.',
            location='Hyderabad',
            date='20 Sep 2026',
            time='10:00 AM',
            status='requested'
        )
        db.session.add(help_request)
        db.session.commit()
        request_id = help_request.id

    try:
        login = client.post('/helper/login', data={'email': 'sindhu@gmail.com', 'password': '123'}, follow_redirects=False)
        assert login.status_code == 302
        assert login.headers['Location'].endswith('/helper/dashboard')

        generic_dashboard = client.get('/dashboard', follow_redirects=False)
        assert generic_dashboard.status_code == 302
        assert generic_dashboard.headers['Location'].endswith('/helper/dashboard')

        accepted = client.post(f'/helper/request/{request_id}/accept', follow_redirects=False)
        assert accepted.status_code == 302
        with app.app_context():
            help_request = db.session.get(HelpRequest, request_id)
            assert help_request.assigned_helper_id == helper_id
            assert help_request.status == 'accepted'
            assert help_request.accepted_at is not None

        started = client.post(f'/helper/request/{request_id}/start', follow_redirects=False)
        assert started.status_code == 302
        completed = client.post(
            f'/helper/request/{request_id}/complete',
            data={'completion_note': 'Groceries delivered.'},
            follow_redirects=False
        )
        assert completed.status_code == 302
        with app.app_context():
            help_request = db.session.get(HelpRequest, request_id)
            assert help_request.status == 'completed'
            assert help_request.completion_note == 'Groceries delivered.'

        logout = client.get('/logout', follow_redirects=False)
        assert logout.status_code == 302
        assert logout.headers['Location'].endswith('/login')
    finally:
        with app.app_context():
            help_request = db.session.get(HelpRequest, request_id)
            if help_request:
                db.session.delete(help_request)
                db.session.commit()
