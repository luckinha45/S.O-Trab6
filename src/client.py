#!/usr/bin/env python3
"""! @brief Example Python program with Doxygen style comments."""
##
# @mainpage Projeto de Sistemas Operacionais - Sistemas Distribuídos
#
# @section description_main Descrição
# Documentação do trabalho 6 da disciplina de Sistemas Operacionais
# @section how_works Como Funciona
# Para testar o sistema, coloque ele em diferentes diretórios e máquinas e abra um terminal no src de cada diretório. Em um dos terminais, entre o comando:<br/>
# > python client.py A.B.C.D PORT1
# - Onde A.B.C.D e PORT1 são, respectivamente, o endereço ip e a porta da máquina.<br/>
# Nos outros outros terminais entre o comando: <br />
# > python client.py E.F.G.H PORT2 A.B.C.D PORT1
# - Onde E.F.G.H PORT2 representam o endereço e porta dessa máquina e A.B.C.D PORT1 representam o endereço e porta da primeira máquina conectada
#
# @section libraries_main Libraries/Modules
# - os e shutil
#   - Lidam com o gerenciamento dos arquivos.
# - threading
#   - Usado para rodar o server em paralelo.
# - xmlrpc
#   - Cria as coneções RPC.
#
# @section author_doxygen_example Autor(es)
# - Criado por Lucas Antonio e Luca Biagini em 30/04/2021.
#
##
# @file client.py
#
# @brief Script que lida com as entradas do usuário.
#
##
# @file server.py
#
# @brief Script que lida com a comunicação com outros usuários.
#
#

# Imports
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import sys
import os
import threading
import shutil
import server as svr

# VARS GLOBAIS
## Thread do server do usuario
svrThr = None

# Funções
def clientHandler():
    """! Lê as entradas do usuário e chama as funções do server p/ executar cada funcionalidade."""
    global svrThr

    while(True):
        print("Opcoes:")
        print("\t1) Listar Arquivos")
        print("\t2) Adicioar novo arquivo")
        print("\t3) Renomear arquivo")
        print("\t4) Remover arquivo")
        print("\t(Para fechar o programa, precione CTRL+C duas vezes)\n")

        while(True):
            try:
                choice = int(input("Qual opcao:\n"))
                break
            except ValueError:
                print("\nEntrada nao eh um numero, tente novamente\n")
                pass

        if choice == 1:
            listFiles = svr.listFiles()
            print("\nAquivos:")
            for listF in listFiles:
                for f in listF["files"]:
                    print('\t' + f)

        elif choice == 2:
            path = input("Insira o caminho do arquivo a ser adicionado:\n")
            if svr.addFile(path):
                print("\nArquivo adicionado ao sistema!")
            else:
                print("\nArquivo nao adicionado ao sistema!")
        
        elif choice == 3:
            oldname = input("\nNome arquivo que sera renomeado:\n")
            newname = input("\nNome novo do arquivo:\n")
            if svr.renameFile(oldname, newname):
                print("\nArquivo Renomeado!")
            else:
                print("\nNao foi possivel renomear o arquivo!")
        
        elif choice == 4:
            filename = input("\nNome arquivo que sera renomeado:\n")
            if svr.removeFile(filename):
                print("\nArquivo Removido!")
            else:
                print("\nNao foi possivel remover o arquivo!")
        
        else:
            print("Escolha invalida\n")
        
        print('\n--------------------------------------\n')
        

def init():
    """! Inicia o cliente."""
    try:
        myHost = sys.argv[1]
        myPort = int(sys.argv[2])
        usrHost = sys.argv[3]
        usrPort = int(sys.argv[4])
    except:
        if len(sys.argv) < 3:
            print("\nEh necessario passar como argumento (obrigatoraimente) endereco e porta desse usuario,")
            print("e (opcional) endereco e porta de outra maquina conectada no sistema. Ex:")
            print("\tCaso queira iniciar um novo sistema:")
            print("\t\tpython app.py localhost 8000\n")
            print("\tCaso queira entrar num sistema ja aberto:")
            print("\t\tpython app.py 172.30.1.29 8000 172.30.1.27 8000")
            print("Onde 172.30.1.29:8000 eh o endereco dessa maquina, e 172.30.1.27:8000 eh o endereco de")
            print("uma maquina ja conectada ao sistema")
            exit(0)
        else:
            usrHost = None
            usrPort = None

    # Criando a pasta dos arquivos
    if os.path.exists('files'):
        shutil.rmtree('files')
    os.mkdir('files')

    # Criando a pasta dos das copias
    if os.path.exists('copies'):
        shutil.rmtree('copies')
    os.mkdir('copies')

    # Removendo a pasta aux, se existir
    if os.path.exists('aux'):
        shutil.rmtree('aux')
    
    # se conecta a rede de usuarios
    svrThr = threading.Thread(target=svr.serverHandler, args=(myHost, myPort, usrHost, usrPort,))
    svrThr.start()

    clientHandler()

if __name__ == "__main__":
    init()