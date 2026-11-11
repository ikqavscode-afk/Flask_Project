"""Скрипты эксплуатации и их рабочие процессы GitHub Actions."""

import http.server
import os
import shutil
import subprocess
import threading
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / 'scripts'
WORKFLOWS = REPO_ROOT / '.github' / 'workflows'

pytestmark = pytest.mark.skipif(shutil.which('bash') is None, reason='нужен bash')


class HealthHandler(http.server.BaseHTTPRequestHandler):
    mode = 'ok'

    def do_GET(self):
        if self.path != '/health':
            self.send_response(404)
            self.end_headers()
            return
        code, body = {
            'ok': (200, b'{"status":"ok"}'),
            'down': (503, b'{"status":"error"}'),
            'foreign': (200, b'<html>not our app</html>'),
        }[type(self).mode]
        self.send_response(code)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    httpd = http.server.HTTPServer(('127.0.0.1', 0), HealthHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


def check(url, attempts='2', pause='0'):
    return subprocess.run(
        [str(SCRIPTS / 'check_health.sh'), url, attempts, pause],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env={**os.environ, 'HEALTH_TIMEOUT': '5'},
    )


@pytest.mark.parametrize('script', sorted(SCRIPTS.glob('*.sh')), ids=lambda p: p.name)
def test_shell_scripts_have_valid_syntax_and_are_executable(script):
    assert os.access(script, os.X_OK)
    assert subprocess.run(['bash', '-n', str(script)], check=False).returncode == 0


def test_health_check_succeeds_for_healthy_site(server):
    HealthHandler.mode = 'ok'

    result = check(f'http://127.0.0.1:{server.server_port}')

    assert result.returncode == 0
    assert 'OK' in result.stdout


@pytest.mark.parametrize('mode', ['down', 'foreign'])
def test_health_check_fails_for_unhealthy_or_foreign_response(server, mode):
    HealthHandler.mode = mode

    result = check(f'http://127.0.0.1:{server.server_port}')

    assert result.returncode == 1
    assert 'НЕДОСТУПЕН' in result.stderr


def test_health_check_fails_when_nothing_listens():
    assert check('http://127.0.0.1:1').returncode == 1


def test_health_check_tolerates_trailing_slash(server):
    HealthHandler.mode = 'ok'

    assert check(f'http://127.0.0.1:{server.server_port}/').returncode == 0


def test_health_check_requires_an_address():
    result = subprocess.run(
        [str(SCRIPTS / 'check_health.sh')], capture_output=True, text=True, check=False
    )

    assert result.returncode != 0


def workflow(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding='utf-8'))


def test_uptime_workflow_runs_on_schedule_and_uses_the_script():
    data = workflow('uptime.yml')
    triggers = data.get(True) or data['on']
    steps = data['jobs']['health']['steps']
    commands = ' '.join(step.get('run', '') for step in steps)

    assert triggers['schedule'][0]['cron']
    assert 'workflow_dispatch' in triggers
    assert 'scripts/check_health.sh' in commands
    assert (SCRIPTS / 'check_health.sh').is_file()


def test_backup_workflow_is_opt_in_and_verifies_restore():
    data = workflow('backup.yml')
    job = data['jobs']['backup']
    steps = job['steps']
    commands = ' '.join(step.get('run', '') for step in steps)
    secret_text = (WORKFLOWS / 'backup.yml').read_text(encoding='utf-8')

    assert "vars.BACKUP_ENABLED == 'true'" in job['if']  # без настройки владельца не запускается
    assert 'scripts/backup_db.sh' in commands
    assert 'RESTORE_CHECK_URL' in secret_text  # восстановление проверяется всегда
    assert 'secrets.BACKUP_DATABASE_URL' in secret_text
    assert 'secrets.BACKUP_PASSPHRASE' in secret_text
    # в файле нет ни одного настоящего адреса базы или пароля
    assert 'render.com' not in secret_text
    uploads = [s for s in steps if str(s.get('uses', '')).startswith('actions/upload-artifact')]
    assert uploads
    assert uploads[0]['with']['path'].endswith('.dump.enc')  # выкладывается только зашифрованное
    assert uploads[0]['with']['retention-days'] <= 30


def test_backup_scripts_never_write_plain_dump_to_disk():
    text = (SCRIPTS / 'backup_db.sh').read_text(encoding='utf-8')

    assert 'pg_dump' in text
    assert '| openssl enc' in text  # дамп сразу шифруется в конвейере
    assert 'pg_dump -Fc --no-owner --no-privileges "$BACKUP_DATABASE_URL" -f' not in text
    assert ' -f ' not in text.split('pg_dump', 1)[1].split('\n', 1)[0]
