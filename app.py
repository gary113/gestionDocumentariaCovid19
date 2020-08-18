import os
from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename
import pypyodbc    
import random

app = Flask(__name__)

app.config['UPLOAD_FOLDER']= "./archivos" #directorio de la carpeta donde estan los archivos

@app.route("/")
def welcome():
    return render_template('MenuPrincipal.html')

@app.route("/tabla")
def contenidotabla():
    connection = pypyodbc.connect('Driver={SQL Server};Server=.;Database=BD_PAGINA')# Creating Cursor    
    cursor = connection.cursor()   
    cursor.execute("SELECT RUTA FROM TESTDOC")   
    s=""
    for row in cursor:
        w=str(row)
        s=s+ w[2:-3] +"&nbsp;&nbsp<a href= " + w[2:-3] + "> Descargar</a> <br><br>" 
    connection.close() 
    return "<html><body>" + s + "</body></html>"  


@app.route("/SubirDocumento.html")
def upload_file():
    return render_template('SubirDocumento.html')

@app.route("/SubirDocumento.html", methods=['POST'])
def uploader():
    if request.method == "POST":
        f = request.files['archivo']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        connection1 = pypyodbc.connect('Driver={SQL Server};Server=.;Database=BD_PAGINA')# Creating Cursor    
        cursor1 = connection1.cursor()
        CODDOC=str(random.randint(1,100))
        TITULO="TESIS N* "+CODDOC
        RUTA="./archivos/"+str(f.filename)
        query="INSERT INTO TESTDOC VALUES ('"+CODDOC+"','"+TITULO+"','"+RUTA+"')"
        cursor1.execute(query)  
        connection1.commit()
        connection1.close()    

        return render_template('SubirDocumento.html') 

@app.route("/Buscador.html")
def buscar():
    return render_template('Buscador.html')

@app.route("/IniciarSesion.html",methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password'].encode('utf-8')
        connection2 = pypyodbc.connect('Driver={SQL Server};Server=.;Database=BD_PAGINA')# Creating Cursor    
        cursor2 = connection2.cursor()
        query="SELECT * FROM USUARIO WHERE CORREO='"+str(email)+"'"
        cursor2.execute(query)  
        user = cursor2.fetchone()
        if user is None:
            connection2.close() 
            return render_template('IniciarSesion.html')
        #return "<html><body>"+ str(user[2]) +"     aaaaaaa"+password.decode("utf-8")+"</body></html>"   
        if password.decode("utf-8")==str(user[2]) :
            session['name']=user[1]
            session['email']=user[3]
            connection2.close() 
            return render_template('MenuInicioUser.html')
        else:
            return render_template('IniciarSesion.html')
    return render_template('IniciarSesion.html')

@app.route("/PublicarDocumento.html")
def document():
    return render_template('PublicarDocumento.html')

@app.route("/ValidarDocumento.html")
def validar():
    return render_template('ValidarDocumento.html')

@app.route("/Documentos.html")
def documentos():
    return render_template('Documentos.html')

@app.route("/MenuPrincipal.html")
def desplegar():
    return render_template('MenuPrincipal.html')

@app.route("/MenuInicioOrg.html")
def desplegar2():
    return render_template('MenuInicioOrg.html')

@app.route("/MenuInicioUser.html")
def desplegar3():
    return render_template('MenuInicioUser.html')

@app.route("/MenuInicioUser/PublicarDocumento.html")
def publicar():
    return render_template('PublicarDocumento.html')


if __name__ == '__main__':
    app.secret_key= 'helloworld'
    app.run(debug=True)