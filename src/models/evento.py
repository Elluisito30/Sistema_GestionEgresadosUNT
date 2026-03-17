"""
Modelo de Evento para el sistema.
Representa un evento (feria, webinar, charla, curso).
"""
from datetime import datetime
from src.utils.database import get_db_cursor
import uuid

class Evento:
    """Clase que representa un evento."""
    
    def __init__(self, id=None, publicado_por=None, titulo=None, descripcion=None, 
                 tipo=None, fecha_inicio=None, fecha_fin=None, lugar=None, 
                 capacidad_maxima=None, es_gratuito=True, precio=0.0, 
                 imagen_promocional_url=None, activo=True):
        self.id = id
        self.publicado_por = publicado_por
        self.titulo = titulo
        self.descripcion = descripcion
        self.tipo = tipo
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.lugar = lugar
        self.capacidad_maxima = capacidad_maxima
        self.es_gratuito = es_gratuito
        self.precio = precio
        self.imagen_promocional_url = imagen_promocional_url
        self.activo = activo

    @staticmethod
    def get_all():
        """Retorna todos los eventos activos."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, publicado_por, titulo, descripcion, tipo, 
                       fecha_inicio, fecha_fin, lugar, capacidad_maxima, 
                       es_gratuito, precio, imagen_promocional_url, activo
                FROM eventos
                WHERE activo = TRUE
                ORDER BY fecha_inicio ASC
            """)
            rows = cur.fetchall()
            return [Evento(*row) for row in rows]

    @staticmethod
    def get_by_id(evento_id):
        """Busca un evento por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM eventos WHERE id = %s", (evento_id,))
            row = cur.fetchone()
            if row:
                columnas = [desc[0] for desc in cur.description]
                return Evento(**dict(zip(columnas, row)))
        return None

    def save(self):
        """Guarda o actualiza el evento."""
        with get_db_cursor(commit=True) as cur:
            if self.id:
                cur.execute("""
                    UPDATE eventos SET
                        publicado_por = %s, titulo = %s, descripcion = %s, 
                        tipo = %s, fecha_inicio = %s, fecha_fin = %s, 
                        lugar = %s, capacidad_maxima = %s, es_gratuito = %s, 
                        precio = %s, imagen_promocional_url = %s, activo = %s
                    WHERE id = %s
                """, (self.publicado_por, self.titulo, self.descripcion, 
                      self.tipo, self.fecha_inicio, self.fecha_fin, 
                      self.lugar, self.capacidad_maxima, self.es_gratuito, 
                      self.precio, self.imagen_promocional_url, self.activo, self.id))
            else:
                self.id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO eventos (id, publicado_por, titulo, descripcion, 
                                       tipo, fecha_inicio, fecha_fin, lugar, 
                                       capacidad_maxima, es_gratuito, precio, 
                                       imagen_promocional_url, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (self.id, self.publicado_por, self.titulo, self.descripcion,
                      self.tipo, self.fecha_inicio, self.fecha_fin, self.lugar,
                      self.capacidad_maxima, self.es_gratuito, self.precio,
                      self.imagen_promocional_url, self.activo))
        return self

    @staticmethod
    def inscribir_usuario(evento_id, usuario_id, pago_id=None):
        """Inscribe a un usuario en un evento."""
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO inscripciones_eventos (evento_id, usuario_id, pago_id)
                    VALUES (%s, %s, %s)
                """, (evento_id, usuario_id, pago_id))
                return True, "Inscripción exitosa"
        except Exception as e:
            if "unique" in str(e).lower():
                return False, "Ya estás inscrito en este evento"
            return False, f"Error al inscribir: {str(e)}"

    @staticmethod
    def get_inscritos(evento_id):
        """Retorna la lista de usuarios inscritos."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT u.id, u.email, ie.fecha_inscripcion, ie.asistio
                FROM inscripciones_eventos ie
                JOIN usuarios u ON ie.usuario_id = u.id
                WHERE ie.evento_id = %s
            """, (evento_id,))
            return cur.fetchall()

    @staticmethod
    def _crear_tabla_chat():
        """Crea la tabla chat_eventos si no existe."""
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_eventos (
                        id SERIAL PRIMARY KEY,
                        evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
                        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                        mensaje TEXT NOT NULL,
                        fecha_envio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_chat_evento_id ON chat_eventos(evento_id);
                    CREATE INDEX IF NOT EXISTS idx_chat_fecha_envio ON chat_eventos(fecha_envio);
                """)
                return True
        except Exception as e:
            print(f"Error al crear tabla chat_eventos: {e}")
            return False

    @staticmethod
    def enviar_mensaje_chat(evento_id, usuario_id, mensaje):
        """Envía un mensaje al chat del evento."""
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO chat_eventos (evento_id, usuario_id, mensaje)
                    VALUES (%s, %s, %s)
                """, (evento_id, usuario_id, mensaje))
                return True, "Mensaje enviado"
        except Exception as e:
            if "relation \"chat_eventos\" does not exist" in str(e):
                if Evento._crear_tabla_chat():
                    return Evento.enviar_mensaje_chat(evento_id, usuario_id, mensaje)
            return False, f"Error al enviar mensaje: {str(e)}"

    @staticmethod
    def get_mensajes_chat(evento_id, limit=100):
        """Obtiene los mensajes del chat de un evento."""
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT ce.mensaje, ce.fecha_envio, u.email, u.rol
                    FROM chat_eventos ce
                    JOIN usuarios u ON ce.usuario_id = u.id
                    WHERE ce.evento_id = %s
                    ORDER BY ce.fecha_envio ASC
                    LIMIT %s
                """, (evento_id, limit))
                return cur.fetchall()
        except Exception as e:
            if "relation \"chat_eventos\" does not exist" in str(e):
                if Evento._crear_tabla_chat():
                    return Evento.get_mensajes_chat(evento_id, limit)
            return []
