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


@app.route("/tabla")
def contenidotabla():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='linux321',
                                 db='BD_PAGINA',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM DOCUMENTO;')
    table = ""
    for row in cursor:
        table = table + row['TITULO_DOCUMENTO'] + '&nbsp;&nbsp;<a href=' + row['RUTA_DOCUMENTO'] + '>Descargar</a><br>'
    connection.close()
    return "<html><body>" + table + "</body></html>"


@app.route("/SubirDocumento.html", methods=['GET', 'POST'])
def subir():
    if request.method == "POST":
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        TITULO = request.form['titulo']
        FECHA = date.today()
        IDIOMA = request.form['idioma']
        ESTADO = 'esp'

        CODIGO_USUARIO = session['codigo_usuario']
        PALABRAS = request.form['palabras'].replace(' ', '').lower().split(',')

        if TITULO != '' and filename[-4:] == '.pdf' and PALABRAS != '':
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

            connection.close()

            return render_template('MenuInicioUser.html', name=session['nombre_usuario'])

        elif filename[-4:] != '.pdf':
            return render_template('SubirDocumento.html', mensaje='Debe subir un documento pdf')

        else:
            return render_template('SubirDocumento.html', mensaje='Debe llenar todos los campos')

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
            cursor.execute('SELECT * FROM DOCUMENTO WHERE COD_DOCUMENTO IN (SELECT DOCUMENTO_COD_DOCUMENTO FROM DOCUMENTO_POR_PALABRA WHERE PALABRAS_CLAVE_COD_PALABRA=(SELECT COD_PALABRA FROM PALABRAS_CLAVE WHERE PALABRA=%s) );', textoBuscar)
            documentosEncontrados = cursor.fetchall()

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
            connection.close()

            if session['tipo_usuario'] == 'adm':
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'])
            else:
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'])

    else:

        if not session:
            return render_template('IniciarSesion.html')
        else:
            if session['tipo_usuario'] == 'adm':
                return render_template('MenuInicioOrg.html', name=session['nombre_usuario'])
            else:
                return render_template('MenuInicioUser.html', name=session['nombre_usuario'])


@app.route("/ValidarDocumento.html")
def validar():
    return render_template('ValidarDocumento.html')


@app.route("/Documentos.html")  # ver para que sirve
def documentos():
    return render_template('Documentos.html')


@app.route("/MenuPrincipal.html")
def desplegar():
    return render_template('MenuPrincipal.html')


@app.route("/MenuInicioOrg.html", methods=['GET'])
def desplegar2():
    if not session:
        return render_template('MenuPrincipal.html')
    else:
        return render_template('MenuInicioOrg.html', name=session['nombre_usuario'])


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
            codBorrar = str(list(request.form.keys())[0])
            cursor.execute('DELETE FROM DOCUMENTO WHERE COD_DOCUMENTO=%s;', codBorrar)
            connection.commit()

        cursor.execute('SELECT * FROM DOCUMENTO WHERE USUARIO_COD_USUARIO=%s', session['codigo_usuario'])
        documentosSubidos = cursor.fetchall()

        return render_template('MenuInicioUser.html', name=session['nombre_usuario'], documentos=documentosSubidos)


@app.route("/PublicarDocumento.html", methods=['GET', 'POST'])
def publicar():
    if request.method == "POST":
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        TITULO = request.form['titulo']
        FECHA = date.today()
        IDIOMA = request.form['idioma']
        VALIDADO = 1

        CODIGO_USUARIO = session['codigo_usuario']
        PALABRAS = request.form['palabras'].split(',')

        if TITULO != '' and filename[-4:] == '.pdf' and PALABRAS != '':
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

            cursor.execute('INSERT INTO DOCUMENTO VALUES (NULL,%s,%s,%s,%s,%s,%s);', (TITULO, RUTA, FECHA, IDIOMA, VALIDADO, CODIGO_USUARIO))
            cursor.execute('SELECT COD_DOCUMENTO FROM DOCUMENTO ORDER BY COD_DOCUMENTO DESC LIMIT 1;')
            cod_documento = cursor.fetchone()['COD_DOCUMENTO']
            connection.commit()

            for palabra in PALABRAS:
                cursor.execute('SELECT * FROM PALABRAS_CLAVE WHERE PALABRA=%s;', palabra)
                palabra_clave = cursor.fetchone()
                if palabra_clave is None:
                    cursor.execute('INSERT INTO PALABRAS_CLAVE VALUES (NULL,%s);', (palabra))
                    connection.commit()

            for palabra in PALABRAS:
                cursor.execute('SELECT COD_PALABRA FROM PALABRAS_CLAVE WHERE PALABRA =%s;', palabra)
                cod_palabra = cursor.fetchone()['COD_PALABRA']
                cursor.execute(
                    'INSERT INTO DOCUMENTO_POR_PALABRA VALUES (%s,%s);', (cod_documento, cod_palabra))
                connection.commit()

            connection.close()

            return render_template('MenuInicioOrg.html', name=session['nombre_usuario'])

        elif filename[-4:] != '.pdf':
            return render_template('PublicarDocumento.html', mensaje='Debe subir un documento pdf')

        else:
            return render_template('PublicarDocumento.html', mensaje='Debe llenar todos los campos')

    else:
        return render_template('PublicarDocumento.html')


@app.route("/CerrarSesion.html", methods=['GET'])
def cerrarSesion():
    session.clear()
    return render_template('MenuPrincipal.html')


if __name__ == '__main__':
    app.secret_key = 'helloworld'
    app.run(debug=True)
