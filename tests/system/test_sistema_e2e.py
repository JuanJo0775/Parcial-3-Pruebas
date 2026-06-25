import httpx


def test_flujo_completo_reserva_y_calculo_total(base_url):
    payload = {
        "cliente_email": "sistema@correo.com",
        "zona": "General",
        "cantidad": 3,
    }

    respuesta_post = httpx.post(
        f"{base_url}/reservas/sistema-evento-xyz", json=payload
    )
    assert respuesta_post.status_code == 201

    respuesta_get = httpx.get(
        f"{base_url}/reservas/sistema-evento-xyz/resumen"
    )
    assert respuesta_get.status_code == 200

    total_recaudado = respuesta_get.json()["total_recaudado"]
    assert total_recaudado == 150_000
