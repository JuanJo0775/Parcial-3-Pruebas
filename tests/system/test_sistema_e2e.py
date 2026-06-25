import httpx

BASE_URL = "http://localhost:8001"


def test_flujo_completo_reserva_y_calculo_total():
    payload = {
        "cliente_email": "sistema@correo.com",
        "zona": "General",
        "cantidad": 3,
    }

    respuesta_post = httpx.post(
        f"{BASE_URL}/reservas/sistema-evento-xyz", json=payload
    )
    assert respuesta_post.status_code == 201

    respuesta_get = httpx.get(
        f"{BASE_URL}/reservas/sistema-evento-xyz/resumen"
    )
    assert respuesta_get.status_code == 200

    total_recaudado = respuesta_get.json()["total_recaudado"]
    assert total_recaudado == 150_000