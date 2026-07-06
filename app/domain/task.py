from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.errors import ValidationError


@dataclass
class Task:
    id: str
    title: str
    done: bool = False
    history: list[str] = field(default_factory=list)

    def complete(self) -> None:
        self.done = True
        self.history.append("completed")


def new_task(task_id: str, title: str) -> Task:
    """Cria uma tarefa validando o título."""
    clean = title.strip()
    if not clean:
        raise ValidationError("título é obrigatório")
    return Task(id=task_id, title=clean, history=["created"])
