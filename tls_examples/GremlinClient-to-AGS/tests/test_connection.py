import subprocess
import tempfile
import shutil
import time
from pathlib import Path
import pytest
import platform


@pytest.mark.slow
def test_tls_connection_with_docker():
    if not shutil.which("bash"):
        pytest.skip("TLS connection test requires bash to be available on PATH")
    if not shutil.which("docker-compose"):
        pytest.skip("TLS connection test requires docker-compose to be available on PATH")
    
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        
        source_dir = Path(__file__).parent.parent
        files_to_copy = ["make-certs.sh", "docker-compose.yaml", "tls_example.py"]
        
        for filename in files_to_copy:
            source_file = source_dir / filename
            if source_file.exists():
                shutil.copy2(source_file, temp_path / filename)
        
        try:
            if platform.system() == "Windows":
                wsl_temp_path = str(temp_path).replace("\\", "/").replace("C:", "/mnt/c")
                
                try:
                    cert_result = subprocess.run(
                        ["wsl", "bash", f"{wsl_temp_path}/make-certs.sh", "exampleCluster"],
                        cwd=str(temp_path),
                        capture_output=True,
                        text=True
                    )
                except FileNotFoundError:
                    cert_result = subprocess.run(
                        ["bash", "-c", f"cd '{temp_path}' && bash make-certs.sh exampleCluster"],
                        cwd=str(temp_path),
                        capture_output=True,
                        text=True
                    )
            else:
                cert_result = subprocess.run(
                    ["bash", "make-certs.sh", "exampleCluster"],
                    cwd=str(temp_path),
                    capture_output=True,
                    text=True
                )
            assert cert_result.returncode == 0, f"Certificate generation failed: {cert_result.stderr}"
            
            security_dir = temp_path / "security"
            gtls_dir = temp_path / "g-tls"
            assert (security_dir / "ca.crt").exists(), "CA certificate not found"
            assert (gtls_dir / "server.crt").exists(), "Server certificate not found"
            
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=str(temp_path),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            print("docker-compose has finished, containers are (re)started.")
            
            print("Waiting for services to start...")
            time.sleep(2)
            

            python_cmd = "python" if platform.system() == "Windows" else "python3"
            connection_result = subprocess.run(
                [python_cmd, "tls_example.py"],
                cwd=temp_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            assert connection_result.returncode == 0, f"TLS connection failed: {connection_result.stderr}"
            
            success_message = "Connected and Queried Successfully, TLS Between AGS and Gremlin is set!"
            assert success_message in connection_result.stdout, f"Success message not found. Output: {connection_result.stdout}"
            
            assert "Testing Connection to Graph" in connection_result.stdout, "Connection test output not found"
            assert "Successfully Connected to Graph" in connection_result.stdout, "Connection success message not found"
            assert "Values:" in connection_result.stdout, "Graph query output not found"
            assert "aerospike" in connection_result.stdout, "Expected vertex property not found"
            
        finally:
            subprocess.run(
                ["docker-compose", "down", "-v"],
                cwd=temp_path,
                capture_output=True
            )
            
    finally:
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            time.sleep(0.1)
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                pass


def test_tls_example_script_exists():
    script_path = Path(__file__).parent.parent / "tls_example.py"
    assert script_path.exists(), "tls_example.py script not found"
    assert script_path.is_file(), "tls_example.py is not a file"


def test_docker_compose_exists():
    compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
    assert compose_path.exists(), "docker-compose.yaml not found"
    assert compose_path.is_file(), "docker-compose.yaml is not a file"


def test_docker_compose_syntax():
    compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
    result = subprocess.run(
        ["docker-compose", "-f", str(compose_path), "config"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"docker-compose config failed: {result.stderr}"


def test_docker_compose_ssl_configuration():
    compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
    content = compose_path.read_text()
    
    assert "aerospike.graph-service.ssl.enabled: true" in content, \
        "SSL configuration not found in docker-compose.yaml"
    
    assert "./g-tls:/opt/aerospike-graph/gremlin-server-tls:ro" in content, \
        "Server certificate mount not found"
    assert "./security/ca.crt:/opt/aerospike-graph/gremlin-server-ca/ca.crt:ro" in content, \
        "CA certificate mount not found" 