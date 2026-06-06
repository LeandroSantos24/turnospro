# app/models/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Importa todos los modelos para que SQLAlchemy y Alembic los detecten.
# Cada vez que agregues un modelo nuevo, importalo acá también.
# ─────────────────────────────────────────────────────────────────────────────

from app.models.empresa          import Empresa, PlanEmpresa, CondicionIVA
from app.models.usuario          import Usuario, RolUsuario
from app.models.cliente          import Cliente, EstadoCliente, NivelFidelizacion
from app.models.trabajador       import Trabajador, EstadoTrabajador
from app.models.categoria        import Categoria
from app.models.servicio         import Servicio, trabajador_servicio
from app.models.turno            import Turno, EstadoTurno, OrigenTurno
from app.models.calificacion     import Calificacion
from app.models.pago             import Pago, MetodoPago, EstadoPago
from app.models.giftcard         import GiftCard, EstadoGiftCard
from app.models.descuento        import Descuento, TipoDescuento
from app.models.historial        import HistorialCliente, TipoEvento
from app.models.mensaje_whatsapp import MensajeWhatsApp
from app.models.notificacion     import Notificacion
from app.models.promocion        import Promocion
from app.models.campana          import CampanaFidelizacion
from app.models.plan_membresia   import PlanMembresia, TipoPlan
from app.models.suscripcion      import SuscripcionCliente, UsoSuscripcion
from app.models.ficha_clinica    import FichaClinica, TipoFicha
from app.models.foto_cliente     import FotoCliente, TipoFoto