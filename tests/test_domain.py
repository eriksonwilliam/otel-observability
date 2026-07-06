import pytest

from app.domain.errors import ValidationError
from app.domain.task import new_task


def test_new_task_trims_and_sets_history():
    task = new_task("t1", "  comprar pão  ")
    assert task.title == "comprar pão"
    assert task.history == ["created"]
    assert task.done is False


def test_new_task_empty_title_raises():
    with pytest.raises(ValidationError):
        new_task("t1", "   ")


def test_complete_marks_done_and_history():
    task = new_task("t1", "tarefa")
    task.complete()
    assert task.done is True
    assert task.history == ["created", "completed"]
