import subprocess
import tempfile
from pathlib import Path
import pytest
import platform

from helpers.util import skip_if_no, get_script_source, copy_script_to, run_make_certs, cleanup_dir

FOLDER_NAME = "AGS-to-AerospikeDB"

def test_tls_connection_with_docker():
    skip_if_no("bash")
    skip_if_no("docker-compose")


    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    try:
        script_src = get_script_source(subdir=FOLDER_NAME)
        script = copy_script_to(temp_path, script_src)

        source_dir = Path(__file__).parent.parent / FOLDER_NAME
        files_to_copy = ["docker-compose.yaml", "aerospike.conf", "tls_example.py"]
        for filename in files_to_copy:
            copy_script_to(temp_path, source_dir / filename)

        result = run_make_certs(script, temp_path)
        assert result.returncode == 0, f"Failure: {result.stderr}"

        security_dir = temp_path / "security"
        assert (security_dir / "ca.crt").exists(), "CA certificate not found"
        assert (security_dir / "server.crt").exists(), "Server certificate not found"
        try:
            docker_proc = subprocess.run(
                ["docker-compose", "up", "-d"],
                check=True,
                cwd=temp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            assert docker_proc.returncode == 0, f"Docker Run failed: {docker_proc.stderr}"
        except:
                print(f"Errored when running docker-compose")
        print("docker-compose has finished, containers are (re)started.")

        python_cmd = "python" if platform.system() == "Windows" else "python3"
        connection_result = subprocess.run(
            [python_cmd, "tls_example.py"],
            cwd=temp_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        assert connection_result.returncode == 0, f"TLS connection failed: {connection_result.stderr}"

        success_message = "Connected and Queried Successfully, TLS between AGS and Aerospike DB is set up!"
        assert success_message in connection_result.stdout, f"Success message not found. Output: {connection_result.stdout}"

        assert "Values:" in connection_result.stdout, "Graph query output not found"
        assert "aerospike" in connection_result.stdout, "Expected vertex property not found"

    finally:
        subprocess.run(
            ["docker-compose", "down", "-v"],
            cwd=temp_path,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        cleanup_dir(temp_path)


def test_tls_example_script_exists():
    script_path = Path(__file__).parent.parent / FOLDER_NAME / "tls_example.py"
    assert script_path.exists(), "tls_example.py script not found"
    assert script_path.is_file(), "tls_example.py is not a file"


def test_docker_compose_exists():
    compose_path = Path(__file__).parent.parent / FOLDER_NAME / "docker-compose.yaml"
    assert compose_path.exists(), "docker-compose.yaml not found"
    assert compose_path.is_file(), "docker-compose.yaml is not a file"