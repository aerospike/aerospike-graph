import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest
import platform
import time


def test_make_certs_script_exists():
    script_path = Path(__file__).parent.parent / "make-certs.sh"
    assert script_path.exists(), "make-certs.sh script not found"
    assert script_path.is_file(), "make-certs.sh is not a file"


def test_certificate_generation():
    if not shutil.which("bash"):
        pytest.skip("Certificate generation test requires bash to be available on PATH")
    
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        
        script_source = Path(__file__).parent.parent / "make-certs.sh"
        script_dest = temp_path / "make-certs.sh"
        shutil.copy2(script_source, script_dest)
        
        if platform.system() == "Windows":
            wsl_script_path = str(script_dest).replace("\\", "/").replace("C:", "/mnt/c")
            
            try:
                result = subprocess.run(
                    ["wsl", "bash", wsl_script_path, "testCluster"],
                    cwd=str(temp_path),
                    capture_output=True,
                    text=True
                )
            except FileNotFoundError:
                result = subprocess.run(
                    ["bash", "-c", f"cd '{temp_path}' && bash '{script_dest}' testCluster"],
                    capture_output=True,
                    text=True
                )
        else:
            result = subprocess.run(
                ["bash", str(script_dest), "testCluster"],
                cwd=temp_path,
                capture_output=True,
                text=True
            )
        
        assert result.returncode == 0, f"make-certs.sh failed: {result.stderr}"
        
        security_dir = temp_path / "security"
        assert security_dir.exists(), "Security directory not created"
        
        security_files = ["ca.crt", "ca.key"]
        for filename in security_files:
            file_path = security_dir / filename
            assert file_path.exists(), f"Security file {filename} not found"
            assert file_path.stat().st_size > 0, f"Security file {filename} is empty"
        
        gtls_dir = temp_path / "g-tls"
        assert gtls_dir.exists(), "g-tls directory not created"
        
        gtls_files = ["server.crt", "server.key"]
        for filename in gtls_files:
            file_path = gtls_dir / filename
            assert file_path.exists(), f"g-tls file {filename} not found"
            assert file_path.stat().st_size > 0, f"g-tls file {filename} is empty"
            
    finally:
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            time.sleep(0.1)
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                pass


def test_certificate_generation_cleanup():
    if not shutil.which("bash"):
        pytest.skip("Certificate generation test requires bash to be available on PATH")
    
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        
        script_source = Path(__file__).parent.parent / "make-certs.sh"
        script_dest = temp_path / "make-certs.sh"
        shutil.copy2(script_source, script_dest)
        
        if platform.system() == "Windows":
            wsl_script_path = str(script_dest).replace("\\", "/").replace("C:", "/mnt/c")
            
            try:
                result = subprocess.run(
                    ["wsl", "bash", wsl_script_path, "testCluster"],
                    cwd=str(temp_path),
                    capture_output=True,
                    text=True
                )
            except FileNotFoundError:
                result = subprocess.run(
                    ["bash", "-c", f"cd '{temp_path}' && bash '{script_dest}' testCluster"],
                    capture_output=True,
                    text=True
                )
        else:
            result = subprocess.run(
                ["bash", str(script_dest), "testCluster"],
                cwd=temp_path,
                capture_output=True,
                text=True
            )
        
        assert result.returncode == 0, f"make-certs.sh failed: {result.stderr}"
        
        intermediate_dir = temp_path / "intermediate"
        assert not intermediate_dir.exists(), "Intermediate directory should be cleaned up"
        
        ca_config = temp_path / "security" / "ca_openssl.cnf"
        assert not ca_config.exists(), "CA config file should be cleaned up"
        
    finally:
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            time.sleep(0.1)
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                pass


def test_certificate_generation_with_custom_cluster():
    if not shutil.which("bash"):
        pytest.skip("Certificate generation test requires bash to be available on PATH")
    
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        
        script_source = Path(__file__).parent.parent / "make-certs.sh"
        script_dest = temp_path / "make-certs.sh"
        shutil.copy2(script_source, script_dest)
        
        custom_name = "myGremlinCluster"
        
        if platform.system() == "Windows":
            wsl_script_path = str(script_dest).replace("\\", "/").replace("C:", "/mnt/c")
            
            try:
                result = subprocess.run(
                    ["wsl", "bash", wsl_script_path, custom_name],
                    cwd=str(temp_path),
                    capture_output=True,
                    text=True
                )
            except FileNotFoundError:
                result = subprocess.run(
                    ["bash", "-c", f"cd '{temp_path}' && bash '{script_dest}' {custom_name}"],
                    capture_output=True,
                    text=True
                )
        else:
            result = subprocess.run(
                ["bash", str(script_dest), custom_name],
                cwd=temp_path,
                capture_output=True,
                text=True
            )
        
        assert result.returncode == 0, f"make-certs.sh with custom cluster failed: {result.stderr}"
        
        security_dir = temp_path / "security"
        gtls_dir = temp_path / "g-tls"
        
        assert (security_dir / "ca.crt").exists(), "CA certificate not created with custom cluster name"
        assert (gtls_dir / "server.crt").exists(), "Server certificate not created with custom cluster name"
        
        if shutil.which("openssl"):
            ca_cert = security_dir / "ca.crt"
            check_result = subprocess.run(
                ["openssl", "x509", "-in", str(ca_cert), "-text", "-noout"],
                capture_output=True,
                text=True
            )
            if check_result.returncode == 0:
                assert custom_name in check_result.stdout, "Custom cluster name not found in certificate"
                
    finally:
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            time.sleep(0.1)
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                pass