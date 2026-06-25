
# Examen Parcial: Pruebas de Integracion, Sistema y E2E
### Pruebas de Software — Ingenieria de Software, Semestre V
### Corporacion Universitaria Empresarial Alexander von Humboldt

Este examen parcial evalua la capacidad de implementar estrategias de pruebas en las capas superiores de la piramide (Integracion, Sistema y E2E) utilizando contenedores y bases de datos reales.

---

## Instrucciones y Reglas de la Evaluacion

* Tiempo maximo: 60 minutos. Administre su tiempo eficientemente.
* Libertad Tecnologica: Para el Punto 4 (Pruebas E2E de Frontend), usted es libre de utilizar la herramienta (Playwright, Cypress, Selenium) y el lenguaje de programacion (Python, TypeScript, JavaScript, Java, etc.) de su preferencia.
* Integridad Academica: Queda estrictamente prohibido el uso de herramientas de Inteligencia Artificial (ChatGPT, Copilot, Gemini, Claude, etc.) y la copia de codigo entre compañeros. Cualquier evidencia de plagio o uso de IA resultara en la anulacion inmediata del parcial (calificacion 0.0) y el respectivo reporte al consejo disciplinario.
* Formato de entrega: Suba un archivo .zip con los archivos solicitados en cada punto a la plataforma indicada antes de que finalice el tiempo.

---

## Contexto de Negocio y Reglas de Dominio

Usted trabajara sobre el sistema TicketFast, una plataforma automatizada de reserva de boletos para eventos masivos. Para este parcial, el backend ya implementa las siguientes reglas de negocio:

1. Catalogo de Zonas y Precios: Los eventos operan estrictamente con dos localidades.
   * VIP: 150.000 COP por asiento.
   * General: 50.000 COP por asiento.
   Cualquier intento de reserva hacia una zona no listada es una operacion invalida para el negocio.
2. Restricciones de Compra: Las transacciones estan ligadas al correo electronico del cliente. Por regla de negocio, toda reserva debe contener como minimo un (1) asiento. No se permiten reservas en cero o con valores negativos.
3. Consolidado Financiero: El sistema tiene la capacidad de auditar financieramente un evento, calculando en tiempo real el gran total recaudado. Este calculo se obtiene multiplicando la cantidad de asientos reservados por el precio correspondiente a la zona de cada cliente, sumando todas las reservas activas del evento.

---

## Codigo Base Proporcionado

Utilice el siguiente codigo de la capa de persistencia y la API como punto de partida. Asuma que este codigo ya compila y las dependencias estan instaladas en su entorno.

### src/database/models.py
```python
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class ReservaDB(Base):
    __tablename__ = "reservas"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evento_id: Mapped[str] = mapped_column(String(50), nullable=False)
    cliente_email: Mapped[str] = mapped_column(String(150), nullable=False)
    zona: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

```

### src/reservas/api.py

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.database.repositorio import ReservasRepositorio
from pydantic import BaseModel

app = FastAPI()

class ReservaInput(BaseModel):
    cliente_email: str
    zona: str
    cantidad: int

@app.post("/reservas/{evento_id}", status_code=201)
def crear_reserva(evento_id: str, reserva: ReservaInput, db: Session = Depends(get_db)):
    if reserva.zona not in ["VIP", "General"]:
        raise HTTPException(status_code=400, detail="Zona invalida")
    if reserva.cantidad < 1:
        raise HTTPException(status_code=400, detail="Cantidad invalida")
        
    repo = ReservasRepositorio(db)
    nueva_reserva = repo.guardar_reserva(evento_id, reserva.cliente_email, reserva.zona, reserva.cantidad)
    return {"mensaje": "Reserva creada con exito", "reserva_id": nueva_reserva.id}

@app.get("/reservas/{evento_id}/resumen", status_code=200)
def obtener_resumen(evento_id: str, db: Session = Depends(get_db)):
    repo = ReservasRepositorio(db)
    total_recaudado = repo.calcular_total_evento(evento_id)
    return {"evento_id": evento_id, "total_recaudado": total_recaudado}

```

---

## Desarrollo del Examen

### Punto 1: Infraestructura de Pruebas (20%)

Para evitar colisiones con el entorno de desarrollo y garantizar una ejecucion limpia, necesitamos un archivo de orquestacion especifico para pruebas.

* Cree unicamente el archivo `docker-compose.test.yml`.
* Defina un servicio `db-test` utilizando la imagen `postgres:16-alpine`.
* Configure este servicio para que almacene los datos temporalmente en la memoria RAM (utilizando `tmpfs` en la ruta de almacenamiento de datos de PostgreSQL: `/var/lib/postgresql/data`) para que la base de datos se destruya inmediatamente al detener el contenedor.
* Defina un servicio `api-test` que dependa de `db-test` y exponga el puerto de pruebas 8001.

### Punto 2: Prueba de Integracion de API (30%)

Asuma que el archivo `conftest.py` ya esta configurado exactamente igual que en el repositorio de clase `carrito-compras`, proporcionando los fixtures `client_con_bd` (que inyecta la sesion de pruebas a FastAPI) y `db_session` (que maneja de forma automatica el aislamiento mediante transacciones y rollback al final de la funcion).

* Cree el archivo `tests/integration/test_api_integracion.py`.
* Escriba una sola funcion de prueba que realice una peticion POST al endpoint `/reservas/concierto-2026` enviando un payload JSON valido (ej. cliente_email: "test@correo.com", zona: "VIP", cantidad: 2).
* La prueba debe incluir dos aserciones obligatorias (asserts):
1. Que el codigo de estado HTTP de la respuesta sea 201 (Created).
2. Que realizando una consulta directa a la base de datos mediante SQLAlchemy usando el fixture `db_session`, el registro del objeto `ReservaDB` efectivamente exista en las tablas, y que el campo `cliente_email` coincida con el valor enviado en la peticion HTTP.



### Punto 3: Prueba de Sistema (20%)

A diferencia de la prueba anterior, las pruebas de sistema no conocen el codigo interno ni tienen acceso a la sesion del ORM o a fixtures de base de datos. Se prueban de extremo a extremo realizando peticiones HTTP a traves de la red contra el servicio real levantado en contenedores.

* Cree el archivo `tests/system/test_sistema_e2e.py`.
* Utilizando exclusivamente la libreria `httpx` apuntando a la URL del contenedor, escriba una prueba que valide el flujo completo y el calculo de la regla de negocio:
1. Haga una peticion POST real para agregar una reserva al evento `sistema-evento-xyz` con zona "General" y cantidad 3.
2. Haga una peticion GET real al endpoint de resumen (`/reservas/sistema-evento-xyz/resumen`) para esa misma sesion de evento.
3. Valide mediante un assert que el campo `total_recaudado` en el JSON de respuesta sea exactamente el valor numerico esperado de acuerdo con la regla de negocio.



### Punto 4: Automatizacion Frontend E2E (30%)

Asuma que el frontend de TicketFast esta corriendo en `http://localhost:4200` y expone un formulario de reserva cuyos elementos son identificables mediante los siguientes atributos de pruebas.

**Selectores disponibles (data-testid):**

* `input-email-cliente` (Campo de texto para el correo)
* `select-zona-evento` (Lista desplegable o input de la zona)
* `input-cantidad-asientos` (Campo numerico de asientos)
* `btn-confirmar-reserva` (Boton para enviar el formulario)
* `seccion-resumen-total` (Contenedor de texto que muestra el valor total calculado en la interfaz)

**Tarea:**

* Cree un script de prueba en la carpeta `tests/e2e/` utilizando la tecnologia y lenguaje de su preferencia.
* Programe las instrucciones para:
1. Navegar a la URL de la interfaz de reservas: `http://localhost:4200/reservas`.
2. Diligenciar el formulario ingresando un correo, seleccionando la zona "VIP" e ingresando la cantidad "1".
3. Hacer clic en el boton de confirmacion.
4. Verificar, utilizando los mecanismos de asercion asincronica y esperas dinamicas nativas de la herramienta elegida (evitando por completo el uso de esperas estaticas o "sleep" manuales), que el elemento `seccion-resumen-total` pase a contener de forma exitosa el texto del valor formateado `"150.000"`.



```

