from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import hashlib, requests, os

# Carregando as variaveis de ambiente, evitar expor no código as infos de conexão.
load_dotenv()

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

#Retorna o icone para o navegador
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')

#Publico login de atendente
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def index():
    
    # Limpando a seção para assegurar o login.
    session.clear()
    
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':

        # Recuperando dados do post realizado pelo formulário
        usuario = request.form['usuario']
        senha = hashMe(request.form['senha'])

        # Consultamos os dados de API
        URL = "https://pi2-api.onrender.com/logar=%s/%s" % (usuario, senha)

        # Consultando a API e transformando a resposta em um objeto pesquisável.
        j = requests.get(URL).json()

        # Verifica a mensagem no Json recebido - Caso positivo
        if j['mensagem'] == 'Login liberado':
            auth = str(j['dados'][0]['Auth'])
            id = str(j['dados'][0]['id'])
            if auth == 'True':
                session['id_atend'] = id
                return redirect(url_for('atendimento'))

        # Verifica a mensagem no Json recebido - Caso negativo  
        elif j['mensagem'] == 'Acesso negado':
            erro = str(j['mensagem'])
            flash('Senha ou usuário incorretos. Tente novamente!')
            return render_template('login.html')
        
        # Para cobrir qualquer outro cenário de erro
        else:
            flash('Algo deu errado. Tente novamente!')
            return redirect(url_for('index'))

    # Para cobrir qualquer outro cenário de erro (redundância)   
    else: 
        flash('Ocorreu algum erro. Tente novamente.')
        return redirect(url_for('index'))

#Após o login feito pelo atendente
@app.route('/atend', methods=['GET','POST'])
def atendimento():

    # Essa rota não pode ser acessada sem o login
    if "id_atend" in session:
        # Caso exista a seção então atribui o id_atend a partir dela
        id_atend = session["id_atend"]
    else:
        return redirect(url_for('index'))

    if request.method == 'GET':
        
        URL = "https://pi2-api.onrender.com/painel"
        table = requests.get(URL)
        table_j = table.json()
        
        return render_template('tabela_atendimento.html', data=table_j)
    
    elif request.method == 'POST':
        
        id_req = ""
        
        # De acordo com o botão acionado vamos realizar um procedimento diferente
        if request.form['botao'] == 'cha':
            # Tem que passar o id do atendente na URL - PUT
            URL = 'https://pi2-api.onrender.com/chamarCliente=%s' % (id_atend)

        elif request.form['botao'] == 'ini':
            # Tem que passar o id do atendente na URL - PUT
            URL = 'https://pi2-api.onrender.com/atenderCliente=%s' % (id_atend)
    
        elif request.form['botao'] == 'enc':
            # Tem que passar o id do atendente na URL - PUT
            URL = 'https://pi2-api.onrender.com/concluirAtendimento=%s' % (id_atend)
           
        elif request.form['botao'] == 'can':
            # Tem que passar o id da requisicao na URL - PUT
            URL = 'https://pi2-api.onrender.com/cancelarAtendimento=%s' % (id_req)
            
        else:
            return render_template('tabela_atendimento.html')
        
        # Realizamos o método PUT na URL
        requests.put(URL)
        return render_template('tabela_atendimento.html')

    else: 
        return render_template('tabela_atendimento.html')

# Publico consulta de painel
@app.route('/painel')
def painel():
    if request.method == 'GET':
        URL = "https://pi2-api.onrender.com/painel"
        table = requests.get(URL)
        table_j = table.json()
        return render_template('painel.html', data=table_j)
    else: 
        return render_template('painel.html')

# Publico acesso via tablet
@app.route('/cliente', methods=['GET','POST'])
def cliente():
    # Ao acessar a rota uma página é exibida com dois botões
    if request.method == 'GET':
        return render_template('tipo_atendimento.html')
    
    # Ao realizar o POST pelos botões
    elif request.method == 'POST':

        # Analisamos o valor do botão pressionado
        if request.form['botao'] == "0":
            # Atendimento prioritário é o botão 0
            URL = 'https://pi2-api.onrender.com/novoCliente=0'
            requests.post(URL)
            
        else:
            # Atencimento convencional é o botão 1
            URL = 'https://pi2-api.onrender.com/novoCliente=1'
            requests.post(URL)
        
        flash("Registrado com sucesso!")
        return render_template('tipo_atendimento.html')

    else: 
        return "<h1>Isso deu errado!</h1>"

#Função de apoio para criptografar em SHA1 a senha antes do envio.
def hashMe(argumento):
    senhaHash = hashlib.sha1(argumento.encode())
    senhaDigest = str(senhaHash.hexdigest())
    return senhaDigest

if __name__ == "__main__":
    app.run()