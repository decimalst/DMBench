import shutil

import pytest

from dataset import ROOT, load_dataset


@pytest.fixture(scope="session")
def bank():
    return load_dataset()


@pytest.fixture
def copied_bank(tmp_path):
    for directory in ("questions", "answers"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copy(ROOT / "dataset.json", tmp_path / "dataset.json")
    return tmp_path
