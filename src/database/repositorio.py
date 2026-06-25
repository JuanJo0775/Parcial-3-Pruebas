from sqlalchemy.orm import Session
from sqlalchemy import select
from src.database.models import ReservaDB

PRECIOS_ZONA = {
    "VIP": 150_000,
    "General": 50_000,
}


class ReservasRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar_reserva(self, evento_id: str, cliente_email: str, zona: str, cantidad: int) -> ReservaDB:
        nueva_reserva = ReservaDB(
            evento_id=evento_id,
            cliente_email=cliente_email,
            zona=zona,
            cantidad=cantidad,
        )
        self.db.add(nueva_reserva)
        self.db.commit()
        self.db.refresh(nueva_reserva)
        return nueva_reserva

    def calcular_total_evento(self, evento_id: str) -> float:
        stmt = select(ReservaDB).where(ReservaDB.evento_id == evento_id)
        reservas = self.db.execute(stmt).scalars().all()

        total = 0
        for reserva in reservas:
            precio_zona = PRECIOS_ZONA.get(reserva.zona, 0)
            total += reserva.cantidad * precio_zona

        return total