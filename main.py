import sqlite3
from flask import Flask, redirect, render_template_string, request, url_for
app = Flask(__name__)
DB_NAME = "ispot.db"
# ---------------------------------------------------------
# BASE DE DATOS Y TABLAS (CLIENTES, INVENTARIO Y GASTOS)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            producto TEXT NOT NULL,
            monto REAL NOT NULL,
            abonado REAL NOT NULL,
            costo_producto REAL DEFAULT 0,
            plan TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventario (
            producto TEXT PRIMARY KEY,
            stock INTEGER NOT NULL,
            costo REAL NOT NULL,
            precio REAL NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL
        )
    """
    )
    cursor.execute("SELECT COUNT(*) FROM inventario")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO inventario VALUES
            ('iPhone 15 Pro Max', 5, 950.0, 1200.0),
            ('AirPods Pro 2', 10, 180.0, 250.0),
            ('MacBook Air M3', 3, 850.0, 1100.0)
        """
        )
        conn.commit()
    conn.close()
init_db()
# ---------------------------------------------------------
# INTERFAZ WEB COMPLETA
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iSPOT Manager Pro</title>
    <style>
        :root {
            --bg-color: #000000;
            --card-bg: #1c1c1e;
            --input-bg: #2c2c2e;
            --accent-gold: #d4af37;
            --text-main: #f5f5f7;
            --text-muted: #86868b;
            --border: #38383a;
            --green: #30d158;
            --red: #ff453a;
            --orange: #ff9f0a;
            --blue: #0a84ff;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 25px; }
        .container { max-width: 1150px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { font-size: 2.2rem; letter-spacing: 3px; margin: 0; color: #fff; font-weight: 700; }
        .header p { color: var(--accent-gold); font-size: 0.85rem; font-weight: 600; letter-spacing: 1.5px; margin-top: 5px; text-transform: uppercase; }
        /* Dashboard Métricas Financieras */
        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 25px; }
        .stat-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 15px 10px; text-align: center; }
        .stat-card .num { font-size: 1.35rem; font-weight: bold; color: var(--accent-gold); }
        .stat-card .num.green { color: var(--green); }
        .stat-card .num.red { color: var(--red); }
        .stat-card .num.orange { color: var(--orange); }
        .stat-card .num.blue { color: var(--blue); }
        .stat-card .label { font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; margin-top: 4px; font-weight: 600; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 22px; margin-bottom: 25px; }
        .card h3 { margin-top: 0; font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 18px; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .form-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .form-grid-gastos { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 12px; }
        input, select { 
            background: var(--input-bg); 
            border: 1px solid var(--border); 
            color: #fff; 
            padding: 10px 12px; 
            border-radius: 8px; 
            font-size: 0.85rem; 
            outline: none; 
            width: 100%; 
            box-sizing: border-box; 
        }
        input:focus, select:focus { border-color: var(--accent-gold); }
        .btn-gold { background: var(--accent-gold); color: #000; font-weight: bold; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; transition: 0.2s; text-align: center; text-decoration: none; }
        .btn-gold:hover { background: #e5be3f; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px 8px; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
        th { color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; }
        .badge { padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; background: #2c2c2e; border: 1px solid var(--border); }
        .btn-action { padding: 5px 8px; font-size: 0.75rem; border-radius: 6px; text-decoration: none; font-weight: 600; margin-right: 2px; display: inline-block; border: none; cursor: pointer; }
        .btn-ws { background: #25d366; color: white; }
        .btn-print { background: #e5be3f; color: black; }
        .btn-edit { background: #0a84ff; color: white; }
        .btn-delete { background: #ff453a; color: white; }
        .search-bar { width: 100%; box-sizing: border-box; margin-bottom: 15px; }
        .grid-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        /* Formulario Inventario Estructurado */
        .inv-form-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .inv-form-row {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr auto;
            gap: 8px;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> iSPOT MANAGER</h1>
            <p>SISTEMA INTEGRAL COMERCIAL, FINANCIERO Y CONTROL DE GASTOS</p>
        </div>
        <!-- Dashboard Financiero -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="num blue">${{ "%.2f"|format(valor_inventario) }}</div>
                <div class="label">Valor Inventario</div>
            </div>
            <div class="stat-card">
                <div class="num">${{ "%.2f"|format(total_ingresos) }}</div>
                <div class="label">Ingreso Cobrado</div>
            </div>
            <div class="stat-card">
                <div class="num orange">${{ "%.2f"|format(total_costos_y_gastos) }}</div>
                <div class="label">Costos + Gastos</div>
            </div>
            <div class="stat-card">
                <div class="num green">${{ "%.2f"|format(ganancia_neta) }}</div>
                <div class="label">Ganancia Neta</div>
            </div>
            <div class="stat-card">
                <div class="num red">${{ "%.2f"|format(total_por_cobrar) }}</div>
                <div class="label">Por Cobrar</div>
            </div>
        </div>
        <!-- Sección Inventario y Gastos -->
        <div class="grid-two-col">
            <!-- Módulo de Inventario -->
            <div class="card">
                <h3>📦 Control de Inventario
                    <button type="button" onclick="toggleFormInventario()" id="btn-toggle-prod" style="background:none; border:none; color:var(--accent-gold); font-weight:bold; cursor:pointer; font-size:0.85rem;">+ Añadir Producto</button>
                </h3>
                <!-- Formulario de Inventario Rediseñado y Cómodo -->
                <form id="form-inventario" action="{{ url_for('agregar_producto') }}" method="POST" style="display:none; margin-bottom:18px; background: rgba(255,255,255,0.03); padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                    <div class="inv-form-container">
                        <div>
                            <input type="text" name="producto" placeholder="Nombre del Equipo Apple (ej: iPhone 15 Pro)" required>
                        </div>
                        <div class="inv-form-row">
                            <input type="number" name="stock" placeholder="Stock (Unids)" required>
                            <input type="number" step="0.01" name="costo" placeholder="Costo ($)" required>
                            <input type="number" step="0.01" name="precio" placeholder="Precio ($)" required>
                            <div style="display:flex; gap:6px;">
                                <button type="submit" class="btn-gold" style="padding: 10px 14px;">Guardar</button>
                                <button type="button" onclick="toggleFormInventario()" style="background: var(--red); color: white; border: none; padding: 10px 12px; border-radius: 8px; cursor: pointer; font-weight: bold;" title="Cerrar">✕</button>
                            </div>
                        </div>
                    </div>
                </form>
                <table>
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Stock</th>
                            <th>Costo ($)</th>
                            <th>Precio ($)</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in inventario %}
                        <tr>
                            <td><b>{{ item.producto }}</b></td>
                            <td><span class="badge" style="color: {{ 'var(--red)' if item.stock < 3 else 'var(--green)' }}">{{ item.stock }} unids</span></td>
                            <td style="color: var(--text-muted);">${{ "%.2f"|format(item.costo) }}</td>
                            <td style="color: var(--accent-gold); font-weight:bold;">${{ "%.2f"|format(item.precio) }}</td>
                            <td>
                                <a href="/eliminar_producto/{{ item.producto }}" class="btn-action btn-delete" onclick="return confirm('¿Quitar producto?')">X</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <!-- Módulo Gastos Operativos -->
            <div class="card">
                <h3>💸 Control de Gastos Operativos</h3>
                <form action="{{ url_for('agregar_gasto') }}" method="POST" style="margin-bottom:15px;">
                    <div class="form-grid-gastos">
                        <input type="text" name="concepto" placeholder="Concepto (ej: Envío DHL)" required>
                        <select name="categoria">
                            <option value="Logística">Logística</option>
                            <option value="Marketing">Marketing</option>
                            <option value="Alquiler/Servicios">Alquiler/Servicios</option>
                            <option value="Otro">Otro</option>
                        </select>
                        <input type="number" step="0.01" name="monto" placeholder="Monto $" required>
                        <button type="submit" class="btn-gold" style="font-size:0.8rem;">Registrar</button>
                    </div>
                </form>
                <table>
                    <thead>
                        <tr>
                            <th>Concepto</th>
                            <th>Categoría</th>
                            <th>Monto</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for g in gastos %}
                        <tr>
                            <td><b>{{ g.concepto }}</b></td>
                            <td><span class="badge">{{ g.categoria }}</span></td>
                            <td style="color: var(--orange); font-weight:bold;">${{ "%.2f"|format(g.monto) }}</td>
                            <td>
                                <a href="/eliminar_gasto/{{ g.id }}" class="btn-action btn-delete" onclick="return confirm('¿Eliminar gasto?')">X</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <!-- Formulario Ventas / Clientes -->
        <div class="card">
            <h3>{{ '✏️ Editar Cliente' if cliente_edit else '➕ Registrar Venta / Cliente' }}</h3>
            <form action="{{ url_for('actualizar', cliente_id=cliente_edit.id) if cliente_edit else url_for('agregar') }}" method="POST">
                <div class="form-grid">
                    <input type="text" name="nombre" placeholder="Nombre cliente" value="{{ cliente_edit.nombre if cliente_edit else '' }}" required>
                    <input type="text" name="telefono" placeholder="Teléfono (ej: 584121234567)" value="{{ cliente_edit.telefono if cliente_edit else '' }}" required>
                    <select name="producto">
                        {% for item in inventario %}
                        <option value="{{ item.producto }}" {{ 'selected' if cliente_edit and cliente_edit.producto == item.producto }}>{{ item.producto }} (Stock: {{ item.stock }} | Venta: ${{ item.precio }})</option>
                        {% endfor %}
                    </select>
                    <input type="number" step="0.01" name="monto" placeholder="Monto Total ($)" value="{{ cliente_edit.monto if cliente_edit else '' }}" required>
                    <input type="number" step="0.01" name="abonado" placeholder="Abonado ($)" value="{{ cliente_edit.abonado if cliente_edit else '' }}" required>
                    <select name="plan">
                        <option value="Pago Contado" {{ 'selected' if cliente_edit and cliente_edit.plan == 'Pago Contado' }}>Pago Contado</option>
                        <option value="SAN (Ahorro)" {{ 'selected' if cliente_edit and cliente_edit.plan == 'SAN (Ahorro)' }}>Plan SAN (Ahorro)</option>
                    </select>
                    <select name="estado">
                        <option value="Registrado 📝" {{ 'selected' if cliente_edit and cliente_edit.estado == 'Registrado 📝' }}>Registrado 📝</option>
                        <option value="En Envío 🚚" {{ 'selected' if cliente_edit and cliente_edit.estado == 'En Envío 🚚' }}>En Envío 🚚</option>
                        <option value="Entregado 📦" {{ 'selected' if cliente_edit and cliente_edit.estado == 'Entregado 📦' }}>Entregado 📦</option>
                    </select>
                    <button type="submit" class="btn-gold" style="grid-column: span 2;">{{ 'Guardar Cambios' if cliente_edit else 'Registrar Venta' }}</button>
                </div>
            </form>
        </div>
        <!-- Tabla Clientes -->
        <div class="card">
            <h3>📋 Base de Datos Comercial</h3>
            <input type="text" id="searchInput" class="search-bar" onkeyup="filtrarTabla()" placeholder="🔍 Buscar por cliente, teléfono o equipo...">
            <table id="clientesTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Cliente</th>
                        <th>Producto</th>
                        <th>Monto</th>
                        <th>Abonado</th>
                        <th>Deuda</th>
                        <th>Estatus</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for c in clientes %}
                    {% set deuda = c.monto - c.abonado %}
                    <tr>
                        <td><span class="badge">{{ c.id }}</span></td>
                        <td><b>{{ c.nombre }}</b></td>
                        <td>{{ c.producto }}</td>
                        <td>${{ "%.2f"|format(c.monto) }}</td>
                        <td style="color: var(--green);">${{ "%.2f"|format(c.abonado) }}</td>
                        <td style="color: {{ 'var(--red)' if deuda > 0 else 'var(--text-muted)' }}; font-weight: bold;">
                            ${{ "%.2f"|format(deuda) }}
                        </td>
                        <td>{{ c.estado }}</td>
                        <td>
                            <a href="https://wa.me/{{ c.telefono }}?text=Hola%20{{ c.nombre }},%20te%20saludamos%20de%20iSPOT.%20Tu%20estado%20de%20cuenta:%20Producto:%20{{ c.producto }}%20|%20Deuda:%20${{ '%.2f'|format(deuda) }}" target="_blank" class="btn-action btn-ws">WhatsApp</a>
                            <button onclick="imprimirRecibo('{{ c.id }}', '{{ c.nombre }}', '{{ c.producto }}', '{{ c.monto }}', '{{ c.abonado }}', '{{ deuda }}')" class="btn-action btn-print">Recibo</button>
                            <a href="/editar/{{ c.id }}" class="btn-action btn-edit">Editar</a>
                            <a href="/eliminar/{{ c.id }}" class="btn-action btn-delete" onclick="return confirm('¿Eliminar registro?')">Quitar</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function toggleFormInventario() {
            var form = document.getElementById("form-inventario");
            var btn = document.getElementById("btn-toggle-prod");
            if (form.style.display === "none" || form.style.display === "") {
                form.style.display = "block";
                btn.innerText = "✕ Cancelar";
                btn.style.color = "var(--red)";
            } else {
                form.style.display = "none";
                btn.innerText = "+ Añadir Producto";
                btn.style.color = "var(--accent-gold)";
            }
        }
        function filtrarTabla() {
            var input = document.getElementById("searchInput");
            var filter = input.value.toUpperCase();
            var table = document.getElementById("clientesTable");
            var tr = table.getElementsByTagName("tr");
            for (var i = 1; i < tr.length; i++) {
                var txtValue = tr[i].textContent || tr[i].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
        function imprimirRecibo(id, cliente, producto, monto, abonado, deuda) {
            var ventana = window.open('', '', 'height=600,width=800');
            ventana.document.write('<html><head><title>Recibo iSPOT</title>');
            ventana.document.write('<style>body{font-family:sans-serif; padding:40px;} .header{text-align:center;} table{width:100%; margin-top:20px; border-collapse:collapse;} td,th{padding:10px; border-bottom:1px solid #ccc;}</style>');
            ventana.document.write('</head><body>');
            ventana.document.write('<div class="header"><h1> iSPOT VENEZUELA</h1><p>COMPROBANTE OFICIAL DE VENTA / SAN</p></div>');
            ventana.document.write('<p><b>Código Transacción:</b> ' + id + '</p>');
            ventana.document.write('<p><b>Cliente:</b> ' + cliente + '</p>');
            ventana.document.write('<table><tr><th>Producto</th><th>Total</th><th>Abonado</th><th>Deuda Pendiente</th></tr>');
            ventana.document.write('<tr><td>' + producto + '</td><td>$' + monto + '</td><td>$' + abonado + '</td><td>$' + deuda + '</td></tr></table>');
            ventana.document.write('<br><br><p style="text-align:center;">¡Gracias por preferir a iSPOT!</p>');
            ventana.document.write('</body></html>');
            ventana.document.close();
            ventana.print();
        }
    </script>
</body>
</html>
"""
# ---------------------------------------------------------
# RUTAS DE CONTROLADORES
# ---------------------------------------------------------
@app.route("/")
def home():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    cursor.execute("SELECT * FROM inventario")
    inventario = cursor.fetchall()
    cursor.execute("SELECT * FROM gastos")
    gastos = cursor.fetchall()
    valor_inventario = sum(i["stock"] * i["costo"] for i in inventario)
    total_ingresos = sum(c["abonado"] for c in clientes)
    costo_mercancia_vendida = sum(c["costo_producto"] for c in clientes)
    total_gastos_operativos = sum(g["monto"] for g in gastos)
    total_costos_y_gastos = (
        costo_mercancia_vendida + total_gastos_operativos
    )
    ganancia_neta = total_ingresos - total_costos_y_gastos
    total_por_cobrar = sum((c["monto"] - c["abonado"]) for c in clientes)
    conn.close()
    return render_template_string(
        HTML_TEMPLATE,
        clientes=clientes,
        inventario=inventario,
        gastos=gastos,
        valor_inventario=valor_inventario,
        total_ingresos=total_ingresos,
        total_costos_y_gastos=total_costos_y_gastos,
        ganancia_neta=ganancia_neta,
        total_por_cobrar=total_por_cobrar,
        cliente_edit=None,
    )
@app.route("/agregar", methods=["POST"])
def agregar():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes")
    count = cursor.fetchone()[0] + 1
    nuevo_id = f"ISP-{count:03d}"
    producto = request.form.get("producto")
    cursor.execute("SELECT costo FROM inventario WHERE producto = ?", (producto,))
    res = cursor.fetchone()
    costo_prod = res["costo"] if res else 0.0
    cursor.execute(
        "INSERT INTO clientes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            nuevo_id,
            request.form.get("nombre"),
            request.form.get("telefono"),
            producto,
            float(request.form.get("monto")),
            float(request.form.get("abonado")),
            costo_prod,
            request.form.get("plan"),
            request.form.get("estado"),
        ),
    )
    cursor.execute(
        "UPDATE inventario SET stock = stock - 1 WHERE producto = ? AND stock > 0",
        (producto,),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
@app.route("/agregar_gasto", methods=["POST"])
def agregar_gasto():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO gastos (concepto, categoria, monto) VALUES (?, ?, ?)",
        (
            request.form.get("concepto"),
            request.form.get("categoria"),
            float(request.form.get("monto")),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
@app.route("/eliminar_gasto/<int:gasto_id>")
def eliminar_gasto(gasto_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO inventario VALUES (?, ?, ?, ?)",
        (
            request.form.get("producto"),
            int(request.form.get("stock")),
            float(request.form.get("costo")),
            float(request.form.get("precio")),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
@app.route("/eliminar_producto/<string:prod_nombre>")
def eliminar_producto(prod_nombre):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventario WHERE producto = ?", (prod_nombre,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
@app.route("/editar/<string:cliente_id>")
def editar(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    cursor.execute("SELECT * FROM inventario")
    inventario = cursor.fetchall()
    cursor.execute("SELECT * FROM gastos")
    gastos = cursor.fetchall()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente_edit = cursor.fetchone()
    valor_inventario = sum(i["stock"] * i["costo"] for i in inventario)
    total_ingresos = sum(c["abonado"] for c in clientes)
    costo_mercancia_vendida = sum(c["costo_producto"] for c in clientes)
    total_gastos_operativos = sum(g["monto"] for g in gastos)
    total_costos_y_gastos = (
        costo_mercancia_vendida + total_gastos_operativos
    )
    ganancia_neta = total_ingresos - total_costos_y_gastos
    total_por_cobrar = sum((c["monto"] - c["abonado"]) for c in clientes)
    conn.close()
    return render_template_string(
        HTML_TEMPLATE,
        clientes=clientes,
        inventario=inventario,
        gastos=gastos,
        valor_inventario=valor_inventario,
        total_ingresos=total_ingresos,
        total_costos_y_gastos=total_costos_y_gastos,
        ganancia_neta=ganancia_neta,
        total_por_cobrar=total_por_cobrar,
        cliente_edit=cliente_edit,
    )
@app.route("/actualizar/<string:cliente_id>", methods=["POST"])
def actualizar(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE clientes 
        SET nombre=?, telefono=?, producto=?, monto=?, abonado=?, plan=?, estado=?
        WHERE id=?
    """,
        (
            request.form.get("nombre"),
            request.form.get("telefono"),
            request.form.get("producto"),
            float(request.form.get("monto")),
            float(request.form.get("abonado")),
            request.form.get("plan"),
            request.form.get("estado"),
            cliente_id,
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
@app.route("/eliminar/<string:cliente_id>")
def eliminar(cliente_id):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == 'postgres':
        cursor.execute("DELETE FROM clientes WHERE id = %s")
    else:
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True, port=5000)