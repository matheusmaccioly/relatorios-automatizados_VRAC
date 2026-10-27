"""Somente arquivos temporários fictícios; nenhum diretório privado institucional."""

import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from vrac.db import private_io


def test_output_is_external_private_and_never_overwrites_existing_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    base = tmp_path / "operator-output"
    run = private_io.create_private_run_directory(base, str(uuid4()), workspace=workspace)
    private_io.write_private_report(run, "diagnose", {"status": "synthetic-test"})
    target = run / "diagnose.json"
    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "synthetic-test"}
    if os.name != "nt":
        assert run.stat().st_mode & 0o777 == 0o700
        assert target.stat().st_mode & 0o777 == 0o600
    with pytest.raises(private_io.PrivateOutputError):
        private_io.write_private_report(run, "diagnose", {"status": "overwrite"})
    assert "overwrite" not in target.read_text(encoding="utf-8")


@pytest.mark.parametrize("location", ["inside", "relative", "private-directory", "invalid-id"])
def test_invalid_output_is_refused_without_metadata_echo(location: str, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    paths = {
        "inside": workspace / "output",
        "relative": Path("relative-sensitive-marker"),
        "private-directory": tmp_path / ".aws" / "output",
        "invalid-id": tmp_path / "output",
    }
    execution_id = "invalid-sensitive-marker" if location == "invalid-id" else str(uuid4())
    with pytest.raises(private_io.PrivateOutputError) as error:
        private_io.create_private_run_directory(paths[location], execution_id, workspace=workspace)
    assert "sensitive-marker" not in str(error.value)


def test_acl_failure_does_not_create_a_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    base = tmp_path / "operator-output"
    execution_id = str(uuid4())

    def fail_permissions(path: Path) -> None:
        raise OSError("private-path-marker")

    monkeypatch.setattr(private_io, "_restrict_directory", fail_permissions)
    with pytest.raises(private_io.PrivateOutputError) as error:
        private_io.create_private_run_directory(base, execution_id, workspace=workspace)
    assert "private-path-marker" not in str(error.value)
    assert not list((base / execution_id).iterdir())


def test_non_catalog_output_name_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(private_io.PrivateOutputError):
        private_io.write_private_report(tmp_path, "../../arbitrary", {})
    assert not list(tmp_path.iterdir())
