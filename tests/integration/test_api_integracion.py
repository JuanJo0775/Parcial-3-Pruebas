from src.database.models import ReservaDB


def test_crear_reserva_la_persiste_en_base_de_datos(client_con_bd, db_session):
    payload = {
        "cliente_email": "test@correo.com",
        "zona": "VIP",
        "cantidad": 2,
    }

    response = client_con_bd.post("/reservas/concierto-2026", json=payload)

    assert response.status_code == 201

    reserva_en_bd = (
        db_session.query(ReservaDB)
        .filter(ReservaDB.evento_id == "concierto-2026")
        .first()
    )

    assert reserva_en_bd is not None
    assert reserva_en_bd.cliente_email == "test@correo.com"