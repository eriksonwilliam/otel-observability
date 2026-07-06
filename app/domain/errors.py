class ValidationError(Exception):
    """Entrada inválida (mapeada para HTTP 400)."""


class NotFoundError(Exception):
    """Recurso inexistente (mapeado para HTTP 404)."""
