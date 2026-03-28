from .payments import router as payments_router
from .schools import router as schools_router
from .guardians import router as guardians_router
from .students import router as students_router
from .invoices import router as invoices_router

__all__ = [
    "payments_router",
    "schools_router",
    "guardians_router",
    "students_router",
    "invoices_router",
]
