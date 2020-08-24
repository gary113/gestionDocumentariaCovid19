import os
from flask import *
from werkzeug.utils import secure_filename
from datetime import date, datetime
import pymysql
import time

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = "./archivos"  # directorio de la carpeta donde estan los archivos


@app.route("/")
def welcome():
    return redirect('MenuPrincipal.html')


@app.route("/SubirDocumento.html", methods=['GET', 'POST'])
def subir():
    if request.method == "POST":
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        TITULO = request.form['titulo']
        FECHA = date.today()
        IDIOMA = request.form['idioma']

        if session['tipo_usuario'] == 'adm':
            ESTADO = 'val'
        else:
            ESTADO = 'esp'

        CODIGO_USUARIO = session['codigo_usuario']
        PALABRAS = request.form['palabras'].replace(' ', '').lower().split(',')

        if TITULO != '' and filename[-4:] == '.pdf' and PALABRAS[0] != '':
            fechaHora = datetime.now()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f"))+"_"+str(filename)))

            RUTA = "./archivos/"+str(fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f"))+"_"+str(filename)

            connection = pymysql.connect(host='localhost',
                                         user='root',
                                         password='linux321',
                                         db='BD_PAGINA',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            cursor = connection.cursor()

            cursor.execute('INSERT INTO DOCUMENTO VALUES (NULL,%s,%s,%s,%s,%s,%s,%s);', (TITULO, FECHA, IDIOMA, ESTADO, RUTA, '-', CODIGO_USUARIO))
            cursor.execute('SELECT COD_DOCUMENTO FROM DOCUMENTO ORDER BY COD_DOCUMENTO DESC LIMIT 1;')
            cod_documento = cursor.fetchone()['COD_DOCUMENTO']
            connection.commit()

            for palabra in PALABRAS:
                cursor.execute('SELECT * FROM PALABRAS_CLAVE WHERE PALABRA=%s;', palabra)
                palabra_clave = cursor.fetchone()
                if palabra_clave is None:
                    cursor.execute('INSERT INTO PALABRAS_CLAVE VALUES (NULL,%s);', palabra)
                    connection.commit()

            for palabra in PALABRAS:
                cursor.execute('SELECT COD_PALABRA FROM PALABRAS_CLAVE WHERE PALABRA =%s;', palabra)
                cod_palabra = cursor.fetchone()['COD_PALABRA']
                cursor.execute(
                    'INSERT INTO DOCUMENTO_POR_PALABRA VALUES (%s,%s);', (cod_documento, cod_palabra))
                connection.commit()

            cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
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
def buscar():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            textoBuscar = request.form['textoBuscar']
            palabras = textoBuscar.replace(' ', '').lower().split(',')
            documentosEncontrados = list()
            for palabra in palabras:
                cursor.execute(
                    'SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO IN (SELECT DOCUMENTO_COD_DOCUMENTO FROM DOCUMENTO_POR_PALABRA WHERE PALABRAS_CLAVE_COD_PALABRA=(SELECT COD_PALABRA FROM PALABRAS_CLAVE WHERE PALABRA=%s) AND ESTADO_DOCUMENTO="val" );', palabra)
                encontrados = cursor.fetchall()
                for encontrado in encontrados:
                    if encontrado not in documentosEncontrados:
                        documentosEncontrados.append(encontrado)

            connection.close()
            return render_template('Buscador.html', documentos=documentosEncontrados)
        else:
            return render_template('Buscador.html')


@app.route("/IniciarSesion.html", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM USUARIO WHERE CORREO_USUARIO=%s;', str(email))
        user = cursor.fetchone()

        if user is None:
            connection.close()
            return render_template('IniciarSesion.html')
        elif password.decode('utf-8') == user['PASSWORD_USUARIO']:
            session['codigo_usuario'] = user['COD_USUARIO']
            session['nombre_usuario'] = user['NOMBRE_USUARIO']
            session['tipo_usuario'] = user['TIPO_USUARIO']

            if session['tipo_usuario'] == 'adm':
                cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)
            else:
                cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)

    else:

        if not session:
            return render_template('IniciarSesion.html')
        else:
            connection = pymysql.connect(host='localhost',
                                         user='root',
                                         password='linux321',
                                         db='BD_PAGINA',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            cursor = connection.cursor()

            if session['tipo_usuario'] == 'adm':
                cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)
            else:
                cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
                documentosSubidos = cursor.fetchall()
                connection.close()
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@app.route("/ValidarDocumento.html", methods=['GET', 'POST'])
def validar():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codValidar = str(list(request.form.keys())[0])
            cursor.execute('SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codValidar)
            documentoValidar = cursor.fetchone()
            connection.close()
            return render_template('DetalleValidar.html', documento=documentoValidar)
        else:
            cursor.execute('SELECT * FROM DOCUMENTO WHERE ESTADO_DOCUMENTO="esp";')
            documentosPendientes = cursor.fetchall()
            connection.close()
            return render_template('ValidarDocumento.html', documentos=documentosPendientes)


@app.route("/DetalleValidar.html", methods=['GET', 'POST'])
def detalleValidar():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codValidar = str(list(request.form.keys())[1])
            accionValidar = request.form[str(codValidar)]
            observaciones = request.form['observaciones']

            if accionValidar == 'Rechazar':
                nuevoEstado = 'rec'
            elif accionValidar == 'Observar':
                nuevoEstado = 'obs'
            else:
                nuevoEstado = 'val'

            cursor.execute('UPDATE DOCUMENTO SET ESTADO_DOCUMENTO=%s, OBSERVACIONES_DOCUMENTO=%s WHERE COD_DOCUMENTO=%s',
                           (nuevoEstado, observaciones, codValidar))
            connection.commit()

            cursor.execute('SELECT * FROM DOCUMENTO WHERE ESTADO_DOCUMENTO="esp";')
            documentosPendientes = cursor.fetchall()
            connection.close()
            return render_template('ValidarDocumento.html', documentos=documentosPendientes)

        else:
            return render_template('DetalleValidar.html')

    return render_template('DetalleValidar.html')


@app.route("/MenuPrincipal.html")
def desplegar():
    return render_template('MenuPrincipal.html')


@app.route("/MenuInicioOrg.html", methods=['GET', 'POST'])
def desplegar2():
    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codBorrar = str(list(request.form.keys())[0])
            cursor.execute('DELETE FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codBorrar)
            connection.commit()

        cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
        documentosSubidos = cursor.fetchall()
        connection.close()

        return render_template('MenuInicioOrg.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@app.route("/MenuInicioUser.html", methods=['GET', 'POST'])
def desplegar3():

    if not session:
        return render_template('MenuPrincipal.html')
    else:
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        if request.method == 'POST':
            codDocumento = str(list(request.form.keys())[0])
            accion = request.form[codDocumento]

            if accion == 'Eliminar':
                cursor.execute('DELETE FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
                connection.commit()
            else:
                cursor.execute('SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
                documentoCorregir = cursor.fetchone()
                return render_template('CorregirDocumento.html', documento=documentoCorregir)

        cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s;', session['codigo_usuario'])
        documentosSubidos = cursor.fetchall()
        connection.close()

        return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@app.route("/CorregirDocumento.html", methods=['POST', 'GET'])
def corregir():

    if request.method == "POST":
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        TITULO = str(request.form['titulo'])
        FECHA = date.today()
        IDIOMA = request.form['idioma']
        ESTADO = 'esp'
        CODIGO_USUARIO = session['codigo_usuario']

        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='linux321',
                                     db='BD_PAGINA',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        codDocumento = str(list(request.form.keys())[2])
        cursor.execute('SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codDocumento)
        documento = cursor.fetchone()

        if TITULO != '' and filename[-4:] == '.pdf':
            fechaHora = datetime.now()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f"))+"_"+str(filename)))

            RUTA = "./archivos/"+str(fechaHora.strftime("%d-%m-%Y_%H-%M-%S-%f"))+"_"+str(filename)

            #codDocumento = str(list(request.form.keys())[0])

            cursor.execute('UPDATE DOCUMENTO SET TITULO_DOCUMENTO = %s, FECHA_SUBIDA = %s, IDIOMA_DOCUMENTO= %s, ESTADO_DOCUMENTO=%s, RUTA_DOCUMENTO=%s WHERE COD_DOCUMENTO=%s;',
                           (TITULO, FECHA, IDIOMA, ESTADO, RUTA, codDocumento))
            connection.commit()

            cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s;', session['codigo_usuario'])
            documentosSubidos = cursor.fetchall()
            connection.close()

            return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)

        elif filename[-4:] != '.pdf':
            return render_template('CorregirDocumento.html', mensaje='Debe subir un documento pdf', documento=documento)

        else:
            return render_template('CorregirDocumento.html', mensaje='Debe llenar todos los campos', documento=documento)


@ app.route("/PublicarDocumento.html", methods=['GET', 'POST'])
def publicar():
    return subir()


@ app.route("/CerrarSesion.html", methods=['GET'])
def cerrarSesion():
    session.clear()
    return render_template('MenuPrincipal.html')


@ app.route('/archivos/<path:filename>', methods=['GET'])
def descargar(filename):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory=uploads, filename=filename)


if __name__ == '__main__':
    app.secret_key = 'helloworld'
    app.run(debug=True)
