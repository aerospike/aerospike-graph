import subprocess
import tempfile
import shutil
from pathlib import Path

from helpers.util import skip_if_no, get_script_source, copy_script_to, run_make_certs, \
    cleanup_dir

FOLDER_NAME = "GremlinClient-to-AGS"

def test_make_certs_script_exists():
    script_path = Path(__file__).parent.parent / FOLDER_NAME / "make-certs.sh"
    assert script_path.exists(), "make-certs.sh script not found"
    assert script_path.is_file(), "make-certs.sh is not a file"


def test_certificate_generation():
    skip_if_no("bash")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    try:
        script_source = get_script_source(subdir=FOLDER_NAME)
        script_dest = copy_script_to(temp_path, script_source)
        result = run_make_certs(script_dest, temp_path)
        assert result.returncode == 0, f"Failure: {result.stderr}"

        ca_cert = temp_path / "security" / "ca.crt"
        server_cert = temp_path / "g-tls" / "server.crt"
        server_key = temp_path / "g-tls" / "server.key"
        for p in (ca_cert, server_cert, server_key):
            assert p.exists(), f"Expected certificate {p.name} not found"

        for cert in (ca_cert, server_cert):
            if shutil.which("openssl"):
                check_result = subprocess.run(
                    ["openssl", "x509", "-in", str(cert), "-text", "-noout"],
                    capture_output=True,
                    text=True
                )
            
    finally:
        cleanup_dir(temp_path)


def test_certificate_generation_cleanup():
    skip_if_no("bash")

    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    try:
        script_source = get_script_source(subdir=FOLDER_NAME)
        script_dest = copy_script_to(temp_path, script_source)
        result = run_make_certs(script_dest, temp_path)
        assert result.returncode == 0, f"Failure: {result.stderr}"

        intermediate_dir = temp_path / "intermediate"
        assert not intermediate_dir.exists(), "Intermediate directory should be cleaned up"
        
        ca_config = temp_path / "security" / "ca_openssl.cnf"
        assert not ca_config.exists(), "CA config file should be cleaned up"
        
    finally:
        cleanup_dir(temp_path)