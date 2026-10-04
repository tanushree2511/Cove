"""The project was renamed (Vision Archive -> Cove): old settings and an old data folder must keep working."""
import os

import pytest

from config import envcompat
from config import vision_config as vc


def test_legacy_env_names_are_accepted_as_aliases(monkeypatch):
    monkeypatch.delenv("COVE_FORCE_CPU", raising=False)
    monkeypatch.setenv("VISION_FORCE_CPU", "1")
    envcompat.apply_legacy_env_aliases()
    assert os.environ["COVE_FORCE_CPU"] == "1"


def test_new_name_wins_over_the_legacy_twin(monkeypatch):
    monkeypatch.setenv("COVE_ORT_THREADS", "6")
    monkeypatch.setenv("VISION_ORT_THREADS", "2")
    envcompat.apply_legacy_env_aliases()
    assert os.environ["COVE_ORT_THREADS"] == "6"


def _legacy_name():
    return vc._LEGACY_APP_DIR


def test_old_data_folder_is_moved_to_the_new_name(tmp_path):
    legacy = tmp_path / _legacy_name()
    legacy.mkdir()
    (legacy / "people_db.json").write_text("{}")
    target = tmp_path / "Cove"
    used = vc._resolve_user_data_dir(str(target))
    assert os.path.normpath(used) == os.path.normpath(str(target))
    assert (target / "people_db.json").read_text() == "{}"
    assert not legacy.exists()


def test_an_empty_new_folder_does_not_block_the_migration(tmp_path):
    # start scripts create the new folder before the app runs
    legacy = tmp_path / _legacy_name()
    legacy.mkdir()
    (legacy / "x.txt").write_text("1")
    (tmp_path / "Cove").mkdir()
    vc._resolve_user_data_dir(str(tmp_path / "Cove"))
    assert (tmp_path / "Cove" / "x.txt").exists()


def test_existing_new_data_is_never_overwritten(tmp_path):
    legacy = tmp_path / _legacy_name()
    legacy.mkdir()
    (legacy / "old.txt").write_text("old")
    target = tmp_path / "Cove"
    target.mkdir()
    (target / "new.txt").write_text("new")
    assert os.path.normpath(vc._resolve_user_data_dir(str(target))) == os.path.normpath(str(target))
    assert (legacy / "old.txt").exists() and (target / "new.txt").exists() and not (target / "old.txt").exists()


def test_if_the_move_is_impossible_the_old_library_is_still_used(tmp_path, monkeypatch):
    legacy = tmp_path / _legacy_name()
    legacy.mkdir()
    (legacy / "old.txt").write_text("old")

    def locked(*a, **k):
        raise PermissionError("in use")

    monkeypatch.setattr(os, "rename", locked)
    used = vc._resolve_user_data_dir(str(tmp_path / "Cove"))
    assert os.path.normpath(used) == os.path.normpath(str(legacy))      # not an empty library


def test_other_folder_names_are_left_alone(tmp_path):
    (tmp_path / _legacy_name()).mkdir()
    custom = tmp_path / "somewhere_else"
    assert os.path.normpath(vc._resolve_user_data_dir(str(custom))) == os.path.normpath(str(custom))
