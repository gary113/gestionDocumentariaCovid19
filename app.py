import os
import time
from datetime import date, datetime

import pymysql
from flask import (Flask, current_app, render_template, request,
                   send_from_directory, session)
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'helloworld'

# directorio de la carpeta donde estan los archivos
app.config['UPLOAD_FOLDER'] = '/home/gary/Proyectos/Python/gestionDocumentariaCovid19/archivos/'
app.config['SRC_FOLDER'] = '/static/src'  # imágenes

HOST = 'localhost'
DB = 'BD_PAGINA'
USER = 'root'


@app.route("/")
@app.route("/MenuPrincipal.html")
def welcome():
    img = os.path.join(app.config['SRC_FOLDER'], 'indice.jpeg')
    return render_template('MenuPrincipal.html', imagen=img)


@app.route("/SubirDocumento.html", methods=['GET', 'POST'])
def subir():
    if request.method == "POST":
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        TITULO = request.form['titulo']
        FECHA = date.today()
        IDIOMA = request.form['idioma']

        if session['tipo_usuario'] == 'adm':
            ESTADO = 'Validado'
        else:
            ESTADO = 'En espera'

        CODIGO_USUARIO = session['codigo_usuario']
        PALABRAS = request.form['palabras'].replace(' ', '').lower().split(',')

        if TITULO != '' and filename[-4:] == '.pdf' and PALABRAS[0] != '':
            fechaHora = datetime.now()

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(
                fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f"))+"_"+str(filename)))

            RUTA = str(fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f")) + \
                "_"+str(filename)

            connection = pymysql.connect(host=HOST,
                                         user=USER,
                                         password='linux321',
                                         db=DB,
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            cursor = connection.cursor()

            cursor.execute('INSERT INTO DOCUMENTO VALUES (NULL,%s,%s,%s,%s,%s,%s,%s);',
                           (TITULO, FECHA, IDIOMA, ESTADO, RUTA, '', CODIGO_USUARIO))
            cursor.execute(
                'SELECT COD_DOCUMENTO FROM DOCUMENTO ORDER BY COD_DOCUMENTO DESC LIMIT 1;')
            cod_documento = cursor.fetchone()['COD_DOCUMENTO']
            connection.commit()

            for palabra in PALABRAS:
                cursor.execute(
                    'SELECT * FROM PALABRAS_CLAVE WHERE PALABRA=%s;', palabra)
                palabra_clave = cursor.fetchone()
                if palabra_clave is None:
                    cursor.execute(
                        'INSERT INTO PALABRAS_CLAVE VALUES (NULL,%s);', palabra)
                    connection.commit()

            for palabra in PALABRAS:
                cursor.execute(
                    'SELECT COD_PALABRA FROM PALABRAS_CLAVE WHERE PALABRA =%s;', palabra)
                cod_palabra = cursor.fetchone()['COD_PALABRA']
                cursor.execute(
                    'INSERT INTO DOCUMENTO_POR_PALABRA VALUES (%s,%s);', (cod_documento, cod_palabra))
                connection.commit()

            cursor.execute(
                'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
            documentosSubidos = cursor.fetchall()
            connection.close()

            if session['tipo_usuario'] == 'adm':
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)
            else:
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)

        elif filename[-4:] != '.pdf':

            if session['tipo_usuario'] == 'adm':
                return render_template('PublicarDocumento.html', mensaje='Debe subir un documento pdf')
            else:
                return render_template('SubirDocumento.html', mensaje='Debe subir un documento pdf')

        else:

            if session['tipo_usuario'] == 'adm':
                return render_template('PublicarDocumento.html', mensaje='Debe llenar todos los campos')
            else:
                return render_template('SubirDocumento.html', mensaje='Debe llenar todos los campos')

    else:

        if session['tipo_usuario'] == 'adm':
            return render_template('PublicarDocumento.html')
        else:
            return render_template('SubirDocumento.html')


@app.route("/Buscador.html", methods=['GET', 'POST'])
@app.route("/BuscadorVisitante.html", methods=['GET', 'POST'])
def buscar():

    connection = pymysql.connect(host=HOST,
                                 user=USER,
                                 password='linux321',
                                 db=DB,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    cursor.execute('SELECT PC.PALABRA FROM DOCUMENTO_POR_PALABRA DPP INNER JOIN PALABRAS_CLAVE PC ON PC.COD_PALABRA=DPP.PALABRAS_CLAVE_COD_PALABRA GROUP BY PC.PALABRA ORDER BY COUNT(*) DESC LIMIT 3;')
    top3 = cursor.fetchall()
    print(top3)

    if request.method == 'POST':
        textoBuscar = request.form['textoBuscar']
        #palabras = textoBuscar.replace(' ', '').lower().split(',')
        palabras = textoBuscar.lower().split(' ')
        documentosEncontrados = list()
        for palabra in palabras:
            cursor.execute(
                'SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO IN (SELECT DOCUMENTO_COD_DOCUMENTO FROM DOCUMENTO_POR_PALABRA WHERE PALABRAS_CLAVE_COD_PALABRA=(SELECT COD_PALABRA FROM PALABRAS_CLAVE WHERE PALABRA=%s) AND ESTADO_DOCUMENTO="Validado" );', palabra)
            encontrados = cursor.fetchall()
            for encontrado in encontrados:
                if encontrado not in documentosEncontrados:
                    documentosEncontrados.append(encontrado)

        connection.close()

        if not session:
            return render_template('BuscadorVisitante.html', top3=top3, documentos=documentosEncontrados)
        else:
            return render_template('Buscador.html', top3=top3, documentos=documentosEncontrados)
    else:
        connection.close()
        if not session:
            return render_template('BuscadorVisitante.html', top3=top3)
        else:
            return render_template('Buscador.html', top3=top3)


@app.route("/IniciarSesion.html", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password='linux321',
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        cursor.execute(
            'SELECT * FROM USUARIO WHERE CORREO_USUARIO=%s;', str(email))
        user = cursor.fetchone()

        if user is None or password == '':
            connection.close()
            return render_template('IniciarSesion.html')
        elif password.decode('utf-8') == user['PASSWORD_USUARIO']:
            session['codigo_usuario'] = user['COD_USUARIO']
            session['nombre_usuario'] = user['NOMBRE_USUARIO']
            session['tipo_usuario'] = user['TIPO_USUARIO']

            if session['tipo_usuario'] == 'adm':
                cursor.execute(
                    'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)
            else:
                cursor.execute(
                    'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)
        connection.close()
        return render_template('IniciarSesion.html')

    else:

        if not session:
            return render_template('IniciarSesion.html')
        else:
            connection = pymysql.connect(host=HOST,
                                         user=USER,
                                         password='linux321',
                                         db=DB,
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            cursor = connection.cursor()

            if session['tipo_usuario'] == 'adm':
                cursor.execute(
                    'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)
            else:
                cursor.execute(
                    'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@app.route("/ValidarDocumento.html", methods=['GET', 'POST'])
def validar():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password='linux321',
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codValidar = str(list(request.form.keys())[0])
            cursor.execute(
                'SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codValidar)
            documentoValidar = cursor.fetchone()
            connection.close()
            return render_template('DetalleValidar.html', documento=documentoValidar)
        else:
            cursor.execute(
                'SELECT * FROM DOCUMENTO WHERE ESTADO_DOCUMENTO="En espera";')
            documentosPendientes = cursor.fetchall()
            connection.close()
            return render_template('ValidarDocumento.html', documentos=documentosPendientes)


@app.route("/DetalleValidar.html", methods=['GET', 'POST'])
def detalleValidar():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password='linux321',
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codValidar = str(list(request.form.keys())[1])
            accionValidar = request.form[str(codValidar)]
            observaciones = request.form['observaciones']

            if accionValidar == 'Rechazar':
                nuevoEstado = 'Rechazado'
            elif accionValidar == 'Observar':
                nuevoEstado = 'Observado'
            else:
                nuevoEstado = 'Validado'

            cursor.execute('UPDATE DOCUMENTO SET ESTADO_DOCUMENTO=%s, OBSERVACIONES_DOCUMENTO=%s WHERE COD_DOCUMENTO=%s',
                           (nuevoEstado, observaciones, codValidar))
            connection.commit()

            cursor.execute(
                'SELECT * FROM DOCUMENTO WHERE ESTADO_DOCUMENTO="En espera";')
            documentosPendientes = cursor.fetchall()
            connection.close()
            return render_template('ValidarDocumento.html', documentos=documentosPendientes)

        else:
            connection.close()
            return render_template('DetalleValidar.html')

    return render_template('DetalleValidar.html')


@app.route("/MenuInicioOrg.html", methods=['GET', 'POST'])
def desplegar2():
    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password='linux321',
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codBorrar = str(list(request.form.keys())[0])
            cursor.execute(
                'SELECT RUTA_DOCUMENTO FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codBorrar)
            archivoEliminar = str(cursor.fetchone()['RUTA_DOCUMENTO'])
            cursor.execute(
                'DELETE FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codBorrar)
            os.remove(os.path.join(
                app.config['UPLOAD_FOLDER'], archivoEliminar))
            connection.commit()

        cursor.execute(
            'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
        documentosSubidos = cursor.fetchall()
        connection.close()

        return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@app.route("/MenuInicioUser.html", methods=['GET', 'POST'])
def desplegar3():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password='linux321',
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codDocumento = str(list(request.form.keys())[0])
            accion = request.form[codDocumento]

            if accion == 'Eliminar':
                cursor.execute(
                    'SELECT RUTA_DOCUMENTO FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
                archivoEliminar = str(cursor.fetchone()['RUTA_DOCUMENTO'])
                cursor.execute(
                    'DELETE FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
                os.remove(os.path.join(
                    app.config['UPLOAD_FOLDER'], archivoEliminar))
                connection.commit()

            else:
                cursor.execute(
                    'SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
                documentoCorregir = cursor.fetchone()
                connection.close()
                return render_template('CorregirDocumento.html', documento=documentoCorregir)

        cursor.execute(
            'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s;', session['codigo_usuario'])
        documentosSubidos = cursor.fetchall()
        connection.close()

        return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@ app.route("/CorregirDocumento.html", methods=['POST', 'GET'])
def corregir():

    if request.method == "POST":
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        TITULO = str(request.form['titulo'])
        FECHA = date.today()
        IDIOMA = request.form['idioma']
        ESTADO = 'En espera'

        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password='linux321',
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        codDocumento = str(list(request.form.keys())[2])
        cursor.execute(
            'SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
        documento = cursor.fetchone()

        if TITULO != '' and filename[-4:] == '.pdf':
            fechaHora = datetime.now()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(
                fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f"))+"_"+str(filename)))
            RUTA = str(fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f")) + \
                "_"+str(filename)

            cursor.execute('UPDATE DOCUMENTO SET TITULO_DOCUMENTO = %s, FECHA_SUBIDA = %s, IDIOMA_DOCUMENTO= %s, ESTADO_DOCUMENTO=%s, RUTA_DOCUMENTO=%s WHERE COD_DOCUMENTO=%s;',
                           (TITULO, FECHA, IDIOMA, ESTADO, RUTA, codDocumento))
            connection.commit()

            os.remove(os.path.join(
                app.config['UPLOAD_FOLDER'], documento['RUTA_DOCUMENTO']))

            cursor.execute(
                'SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s;', session['codigo_usuario'])
            documentosSubidos = cursor.fetchall()
            connection.close()

            return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)

        elif filename[-4:] != '.pdf':
            connection.close()
            return render_template('CorregirDocumento.html', mensaje='Debe subir un documento pdf', documento=documento)

        else:
            connection.close()
            return render_template('CorregirDocumento.html', mensaje='Debe llenar todos los campos', documento=documento)


@ app.route("/PublicarDocumento.html", methods=['GET', 'POST'])
def publicar():
    return subir()


@ app.route("/CerrarSesion.html", methods=['GET'])
def cerrarSesion():
    session.clear()
    return welcome()


@ app.route('/<path:filename>', methods=['GET'])
def descargar(filename):
    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], filename=filename, as_attachment=True)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.config['SRC_FOLDER'], 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.secret_key = 'helloworld'
    app.run(debug=True)
