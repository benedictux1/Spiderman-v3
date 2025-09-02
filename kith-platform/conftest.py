import os
import tempfile
import shutil
import pytest

@pytest.fixture(autouse=True, scope="session")
def test_env_isolation():
    db_fd, db_path = tempfile.mkstemp(prefix="kith_test_", suffix=".db")
    os.close(db_fd)
    chroma_dir = tempfile.mkdtemp(prefix="kith_chroma_test_")

    os.environ["KITH_DB_PATH"] = db_path
    os.environ["CHROMA_DB_PATH"] = chroma_dir
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")

    yield

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass
    try:
        shutil.rmtree(chroma_dir, ignore_errors=True)
    except Exception:
        pass 