from playwright.sync_api import Page, expect

URL_RESERVAS = "http://localhost:4200/reservas.html"


def test_reserva_vip_actualiza_resumen_total(page: Page):
    page.goto(URL_RESERVAS)

    page.get_by_test_id("input-email-cliente").fill("cliente@correo.com")
    page.get_by_test_id("select-zona-evento").select_option("VIP")
    page.get_by_test_id("input-cantidad-asientos").fill("1")

    page.get_by_test_id("btn-confirmar-reserva").click()

    resumen = page.get_by_test_id("seccion-resumen-total")
    expect(resumen).to_contain_text("150.000", timeout=5000)