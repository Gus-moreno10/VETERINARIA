import os
import sqlite3
from flask import Flask, flash, g, redirect, render_template, request, url_for


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "citas.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "veterinaria-secret-key"

HORARIOS_DISPONIBLES = [
    "08:00 AM",
    "09:00 AM",
    "10:00 AM",
    "11:00 AM",
    "12:00 PM",
    "01:00 PM",
    "02:00 PM",
    "03:00 PM",
    "04:00 PM",
]
# creando la funcion get db

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascota TEXT NOT NULL,
            propietario TEXT NOT NULL,
            especie TEXT,
            fecha TEXT NOT NULL
        )
        """
    )
    db.commit()


def separar_fecha_hora(fecha_guardada):
    partes = fecha_guardada.rsplit(" ", 2)
    if len(partes) == 3:
        return f"{partes[0]}", f"{partes[1]} {partes[2]}"
    return fecha_guardada, ""


@app.route("/")
def index():
    init_db()
    db = get_db()
    citas = db.execute(
        "SELECT id, mascota, propietario, especie, fecha FROM pacientes ORDER BY fecha"
    ).fetchall()
    return render_template("index.html", citas=citas)


@app.route("/agendar", methods=["GET", "POST"])
def agendar():
    if request.method == "POST":
        mascota = request.form["mascota"].strip()
        propietario = request.form["propietario"].strip()
        especie = request.form["especie"].strip()
        fecha_base = request.form["fecha"].strip()
        hora = request.form["hora"].strip()
        fecha = f"{fecha_base} {hora}" if fecha_base and hora else ""

        if not mascota or not propietario or not fecha_base or not hora:
            flash("Mascota, propietario, fecha y hora son obligatorios.", "danger")
            return render_template("agendar.html", horarios=HORARIOS_DISPONIBLES)

        db = get_db()
        db.execute(
            """
            INSERT INTO pacientes (mascota, propietario, especie, fecha)
            VALUES (?, ?, ?, ?)
            """,
            (mascota, propietario, especie, fecha),
        )
        db.commit()
        flash("La cita fue registrada correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("agendar.html", horarios=HORARIOS_DISPONIBLES)


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    db = get_db()
    cita = db.execute(
        "SELECT id, mascota, propietario, especie, fecha FROM pacientes WHERE id = ?",
        (id,),
    ).fetchone()

    if cita is None:
        flash("La cita solicitada no existe.", "warning")
        return redirect(url_for("index"))

    fecha_base, hora = separar_fecha_hora(cita["fecha"])

    if request.method == "POST":
        mascota = request.form["mascota"].strip()
        propietario = request.form["propietario"].strip()
        especie = request.form["especie"].strip()
        fecha_base = request.form["fecha"].strip()
        hora = request.form["hora"].strip()
        fecha = f"{fecha_base} {hora}" if fecha_base and hora else ""

        if not mascota or not propietario or not fecha_base or not hora:
            flash("Mascota, propietario, fecha y hora son obligatorios.", "danger")
            cita_editada = dict(cita)
            cita_editada["fecha_base"] = fecha_base
            cita_editada["hora"] = hora
            return render_template(
                "editar.html",
                cita=cita_editada,
                horarios=HORARIOS_DISPONIBLES,
            )

        db.execute(
            """
            UPDATE pacientes
            SET mascota = ?, propietario = ?, especie = ?, fecha = ?
            WHERE id = ?
            """,
            (mascota, propietario, especie, fecha, id),
        )
        db.commit()
        flash("La cita fue actualizada correctamente.", "success")
        return redirect(url_for("index"))

    cita_data = dict(cita)
    cita_data["fecha_base"] = fecha_base
    cita_data["hora"] = hora
    return render_template("editar.html", cita=cita_data, horarios=HORARIOS_DISPONIBLES)


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    db = get_db()
    db.execute("DELETE FROM pacientes WHERE id = ?", (id,))
    db.commit()
    flash("La cita fue cancelada correctamente.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
