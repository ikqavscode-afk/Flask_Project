"""Проверки файла публикации render.yaml: ошибка в нём сорвала бы первую выкатку."""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RENDER_FILE = REPO_ROOT / 'render.yaml'


@pytest.fixture(scope='module')
def blueprint():
    return yaml.safe_load(RENDER_FILE.read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def web(blueprint):
    services = [s for s in blueprint['services'] if s['type'] == 'web']
    assert len(services) == 1
    return services[0]


def env_vars(service):
    return {item['key']: item for item in service['envVars']}


def test_blueprint_file_exists_at_repo_root():
    assert RENDER_FILE.is_file()


def test_docker_paths_exist_relative_to_repo_root(web):
    dockerfile = REPO_ROOT / web['dockerfilePath']
    context = REPO_ROOT / web['dockerContext']

    assert web['runtime'] == 'docker'
    assert dockerfile.is_file()
    assert context.is_dir()
    assert dockerfile.parent == context  # Dockerfile лежит в контексте сборки


def test_health_check_path_is_served_by_the_app(web, client):
    assert client.get(web['healthCheckPath']).status_code == 200


def test_deploys_only_after_ci_checks_pass(web):
    assert web['autoDeployTrigger'] == 'checksPass'


def test_required_environment_variables_are_declared(web):
    variables = env_vars(web)

    assert variables['APP_ENV']['value'] == 'production'
    assert variables['SECRET_KEY']['generateValue'] is True
    assert 'PORT' in variables


def test_secret_key_is_generated_not_hardcoded(web):
    secret = env_vars(web)['SECRET_KEY']

    assert 'value' not in secret


def test_database_url_comes_from_declared_database(blueprint, web):
    database_names = {db['name'] for db in blueprint['databases']}
    source = env_vars(web)['DATABASE_URL']['fromDatabase']

    assert source['name'] in database_names
    assert source['property'] == 'connectionString'


def test_no_secrets_are_written_into_the_file(blueprint):
    text = RENDER_FILE.read_text(encoding='utf-8')

    # адреса баз с паролем и ключи известных форматов
    assert not re.search(r'postgres(ql)?://\S+:\S+@', text)
    assert not re.search(r'\bsk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}', text)

    # значения секретных переменных не задаются в файле
    secret_words = ('SECRET', 'PASSWORD', 'TOKEN', 'KEY', 'DSN', 'DATABASE_URL')
    for service in blueprint['services']:
        for item in service['envVars']:
            if any(word in item['key'] for word in secret_words):
                assert 'value' not in item, item['key']


def test_dockerfile_listens_on_port_variable():
    dockerfile = (REPO_ROOT / 'flask-diary' / 'Dockerfile').read_text(encoding='utf-8')

    assert '0.0.0.0:${PORT}' in dockerfile


def test_database_version_matches_ci(blueprint):
    ci = (REPO_ROOT / '.github' / 'workflows' / 'tests.yml').read_text(encoding='utf-8')
    version = blueprint['databases'][0]['postgresMajorVersion']

    assert f'image: postgres:{version}' in ci
