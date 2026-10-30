import pytest

from nilmodel import db


@pytest.fixture
def con():
    c = db.connect(":memory:")
    db.init_db(c)
    yield c
    c.close()
