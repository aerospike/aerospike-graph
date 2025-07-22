"""
Test TLS connection for GremlinClient-to-AGS example.
"""
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
import pytest
import platform
import os


@pytest.mark.slow
def test_tls_connection_with_docker():
    """Test complete TLS connection from Gremlin client to AGS via secure WebSocket."""
    # Check if bash and docker-compose are available
    if not shutil.which("bash"):
        pytest.skip("TLS connection test requires bash to be available on PATH")
    if not shutil.which("docker-compose"):
        pytest.skip("TLS connection test requires docker-compose to be available on PATH")
    
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        
        # Copy all necessary files to temp directory
        source_dir = Path(__file__).parent.parent
        files_to_copy = ["make-certs.sh", "docker-compose.yaml", "tls_example.py"]
        
        for filename in files_to_copy:
            source_file = source_dir / filename
            if source_file.exists():
                shutil.copy2(source_file, temp_path / filename)
        
        try:
            # Step 1: Generate certificates
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
            
            # Verify certificates exist in both directories
            security_dir = temp_path / "security"
            gtls_dir = temp_path / "g-tls"
            assert (security_dir / "ca.crt").exists(), "CA certificate not found"
            assert (gtls_dir / "server.crt").exists(), "Server certificate not found"
            
            # Step 2: Start Docker containers
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=str(temp_path),
                check=True,          # fail loudly on error
                stdout=subprocess.PIPE,  # or None if you don't care about output
                stderr=subprocess.STDOUT,
                text=True            # get strings instead of bytes
            )

            print("docker-compose has finished, containers are (re)started.")
            
            # Step 3: Wait for services to be ready
            print("Waiting for services to start...")
            time.sleep(2)  # Give services time to start and establish SSL
            
            # Step 4: Test secure TLS connection
            # Use python instead of python3 on Windows
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            connection_result = subprocess.run(
                [python_cmd, "tls_example.py"],
                cwd=temp_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Verify connection was successful
            assert connection_result.returncode == 0, f"TLS connection failed: {connection_result.stderr}"
            
            # Check for success message
            success_message = "Connected and Queried Successfully, TLS Between AGS and Gremlin is set!"
            assert success_message in connection_result.stdout, f"Success message not found. Output: {connection_result.stdout}"
            
            # Verify graph operations worked
            assert "Testing Connection to Graph" in connection_result.stdout, "Connection test output not found"
            assert "Successfully Connected to Graph" in connection_result.stdout, "Connection success message not found"
            assert "Values:" in connection_result.stdout, "Graph query output not found"
            assert "aerospike" in connection_result.stdout, "Expected vertex property not found"
            
        finally:
            # Cleanup Docker containers
            subprocess.run(
                ["docker-compose", "down", "-v"],
                cwd=temp_path,
                capture_output=True
            )
            
    finally:
        # Manual cleanup for Windows compatibility
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            time.sleep(0.1)
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                pass  # Ignore if we can't clean up


def test_tls_example_script_exists():
    """Test that tls_example.py script exists."""
    script_path = Path(__file__).parent.parent / "tls_example.py"
    assert script_path.exists(), "tls_example.py script not found"
    assert script_path.is_file(), "tls_example.py is not a file"


def test_docker_compose_exists():
    """Test that docker-compose.yaml exists."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
    assert compose_path.exists(), "docker-compose.yaml not found"
    assert compose_path.is_file(), "docker-compose.yaml is not a file"


def test_docker_compose_syntax():
    """Test that docker-compose.yaml has valid syntax."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
    result = subprocess.run(
        ["docker-compose", "-f", str(compose_path), "config"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"docker-compose config failed: {result.stderr}"


def test_docker_compose_ssl_configuration():
    """Test that docker-compose.yaml contains SSL configuration."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
    content = compose_path.read_text()
    
    # Check for SSL environment variable
    assert "aerospike.graph-service.ssl.enabled: true" in content, \
        "SSL configuration not found in docker-compose.yaml"
    
    # Check for certificate volume mounts
    assert "./g-tls:/opt/aerospike-graph/gremlin-server-tls:ro" in content, \
        "Server certificate mount not found"
    assert "./security/ca.crt:/opt/aerospike-graph/gremlin-server-ca/ca.crt:ro" in content, \
        "CA certificate mount not found" 