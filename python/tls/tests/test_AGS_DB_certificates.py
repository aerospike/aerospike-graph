import subprocess
import tempfile
import shutil
from pathlib import Path

from helpers.util import (get_script_source, copy_script_to, run_make_certs, cleanup_dir, skip_if_no)
FOLDER_NAME = "AGS-to-AerospikeDB"

def test_make_certs_script_exists():
    script_path = Path(__file__).parent.parent / FOLDER_NAME /  "make-certs.sh"
    assert script_path.exists(), "make-certs.sh script not found"
    assert script_path.is_file(), "make-certs.sh is not a file"


def test_certificate_generation():
    skip_if_no("bash")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    try:
        script_src = get_script_source(subdir=FOLDER_NAME)
        script = copy_script_to(temp_path, script_src)
        result = run_make_certs(script, temp_path)
        assert result.returncode == 0, f"Failure: {result.stderr}"

        ca_cert = temp_path / "security" / "ca.crt"
        server_cert = temp_path / "security" / "server.crt"
        server_key = temp_path / "security" / "server.key"
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