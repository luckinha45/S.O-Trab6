from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import sys
import os
import threading
import socket
from time import sleep
import shutil
import base64

# VARS GLOBAIS
## Endereço do usuário
host = ""

## Porta do usuário
port = 8000

## Socket do server
server = None

# allUsers tem a seguinte estrutura:
# [
#   { "host": addr, "port": port1 },
#   { "host": addr, "port": port2 }, etc
# ]

## Lista dos usuários conectados 
allUsers = []

#region FUNCOES REGISTRADAS NO RPC

def rpc_connToUser(usrHost, usrPort):
    """! Avisa ao usuário que outro usuário quer entrar na conexão.

    @param usrHost host do usuario que quer se conectar.
    @param usrPort porta do usuário que quer se conectar.
    """

    global host, port

    if len(allUsers) > 4:
        return None
    
    # avisa aos outros usuarios q um novo usuario quer entrar na conexao
    for user in allUsers:
        if (user["host"] != host) or (user["port"] != port):
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                proxy.rpc_newUser(usrHost, usrPort)
    
    rpc_newUser(usrHost, usrPort)
    return allUsers

def rpc_removeUser(host, port):
    """! Remove um usuário da lista allUsers.

    @param host host do usuario que será deletado.
    @param port porta do usuário que será deletado.
    """

    allUsers.remove({ "host": host, "port": port })

def rpc_getFilesList():
    """! Retorna a lista de arquivos dentro da pasta files."""
    global host, port
    return { "files": os.listdir('files'), "host": host, "port": port }

def rpc_getCopiesList():
    """! Retorna a lista de arquivos dentro da pasta copies."""
    global host, port
    return { "files": os.listdir('copies'), "host": host, "port": port }

def rpc_getFilesTotalSize(filename):
    """! Calcula a soma dos tamanhos das pastas files e copies, e verifica se existe um arquivo com o nome igual ao parametro filename.

    @param filename nome do arquivo que vai ser inserido no futuro.

    @return se filename não existe nesse usuário, retorna a soma dos tamanhos das pastas files e copies. Se não, retorna None.
    """

    if not os.path.exists('./files/'+filename):
        filesSize = sum(d.stat().st_size for d in os.scandir('./files') if d.is_file())
        copiesSize = sum(d.stat().st_size for d in os.scandir('./copies') if d.is_file())

        return filesSize + copiesSize
    
    return None

def rpc_receiveNewFile(fileName, fileData, isCopy):
    """! Cria e escreve o nome recebido.
    
    @param fileName Nome do arquivo a ser inserido.
    @param fileData Conteúdo do arquivo a ser inserido.
    @param isCopy Se for true, o arquivo é salvo na pasta copies, se não, é salvo na pasta files.
    """

    f = None
    if not isCopy:
        f = open('./files/'+fileName, "wb")
    else:
        f = open('./copies/'+fileName, "wb")
    
    try:
        f.write(fileData.data)
    except:
        f.write(fileData)
    
    f.close()
    print(f"\nrecebido { ('arquivo', 'copia')[isCopy] } {fileName}")
    pass

def rpc_fromCopyToFile(filename):
    """! Remove uma cópia e o readiciona como um arquivo normal.
    
    @param filename nome do arquivo a ser alterado.
    """

    os.mkdir('aux')

    shutil.move('./copies/'+filename, './aux/'+filename)
    addFile('./aux/'+filename)
    
    shutil.rmtree('aux')

def rpc_newUser(host, port):
    """! Registra novo usuário conectado.
    
    @param host Host do novo usuário.
    @param port Porta do novo usuário.
    """
    allUsers.append( {"host": host, "port": port} )

def rpc_renameFile(oldname, newname):
    """! Renomeia um arquivo dentro da pasta files.
    
    @param oldname Nome atual do arquivo a ser renomeado.
    @param newname Nome novo do arquivo a ser renomeado.
    """

    if os.path.exists('./files/'+oldname):
        shutil.move('./files/'+oldname, './files/'+newname)
        return True

    else:
        return False

def rpc_renameCopy(oldname, newname):
    """! Renomeia um arquivo dentro da pasta copies.
    
    @param oldname Nome atual do arquivo a ser renomeado.
    @param newname Nome novo do arquivo a ser renomeado.
    """

    if os.path.exists('./copies/'+oldname):
        shutil.move('./copies/'+oldname, './copies/'+newname)
        return True

    else:
        return False

def rpc_removeFile(filename):
    """! Remove um arquivo dentro da pasta files.
    
    @param filename Nome do arquivo a ser removido.
    """

    if os.path.exists('./files/'+filename):
        os.remove('./files/'+filename)
        return True

    else:
        return False

def rpc_removeCopy(filename):
    """! Remove um arquivo dentro da pasta copies.
    
    @param filename Nome do arquivo a ser removido.
    """

    if os.path.exists('./copies/'+filename):
        os.remove('./copies/'+filename)
        return True

    else:
        return False

#endregion

def listFiles():
    """! Lista os arquivos de todos os usuários na pasta files.
    
    @return Retorna a lista de arquivos.
    """

    files = []
    for user in allUsers:
        try:
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                files.append(proxy.rpc_getFilesList())
        except:
            userDropped(user['host'], user['port'])
            return listFiles()
    return files

def listCopies():
    """! Lista os arquivos de todos os usuários na pasta copeis.
    
    @return Retorna a lista de arquivos.
    """

    copies = []
    for user in allUsers:
        try:
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                copies.append(proxy.rpc_getCopiesList())
        except:
            userDropped(user['host'], user['port'])
    return copies

def addFile(path):
    """! Adicona um arquivo no sistema distribuído.
    
    @param path Caminho do arquivo a ser adicionado.

    @return Retorna True se a operação foi bem-sucedida, ou False caso contrário.
    """

    global host, port
    sizes = []
    fileName = os.path.basename(path)

    # verificando o tamanho da pasta files de cada usuario e se existe algum arquivo de mesmo nome
    for user in allUsers:
        if (user["host"] != host) or (user["port"] != port):
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                size = proxy.rpc_getFilesTotalSize(fileName)
                if size != None:
                    sizes.append([ size, user['host'], user['port'] ])
                else:
                    # se retornou None, arquivo com msm nome ja existe nesse usuario
                    return False
        else:
            size = rpc_getFilesTotalSize(fileName)
            if size != None:
                sizes.append([ size, host, port ])
            else:
                # se retornou None, arquivo com msm nome ja existe nesse usuario
                return False

    f = open(path, "rb")
    fileData = bytes(f.read())
    
    f.close()

    # pegando o usuario com o menor files e copies, e enviando o arquivo pra esse usuario
    sizes.sort(key=lambda size: size[0])

    if (sizes[0][1] != host) or (sizes[0][2] != port):
        with xmlrpc.client.ServerProxy(f"http://{sizes[0][1]}:{sizes[0][2]}/", allow_none=True) as proxy:
            proxy.rpc_receiveNewFile(fileName, fileData, False)
    else:
        rpc_receiveNewFile(fileName, fileData, False)
    

    #Enviando a copia p/ o outro usuario com o menor files e copies
    if (sizes[1][1] != host) or (sizes[1][2] != port):
        with xmlrpc.client.ServerProxy(f"http://{sizes[1][1]}:{sizes[1][2]}/", allow_none=True) as proxy:
            proxy.rpc_receiveNewFile(fileName, fileData, True)
    else:
        rpc_receiveNewFile(fileName, fileData, True)

    
    print(f"Arquivo enviado p/ {sizes[0][1]}:{sizes[0][2]}")
    return True

def renameFile(oldname, newname):
    """! Renomeia um arquivo no sistema distribuído.
    
    @param oldname Nome do arquivo a ser renomeado.
    @param newname Novo nome do arquivo a ser renomeado.

    @return Retorna True se a operação foi bem-sucedida, ou False caso contrário.
    """

    fileChanged = False
    CopyChanged = False
    for user in allUsers:
        if not fileChanged:
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                fileChanged = proxy.rpc_renameFile(oldname, newname)
        
        if not CopyChanged:
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                CopyChanged = proxy.rpc_renameCopy(oldname, newname)
        
        if fileChanged and CopyChanged:
            return True
    
    return False

def removeFile(filename):
    """! Remove um arquivo no sistema distribuído.
    
    @param filename Nome do arquivo a ser removido.

    @return Retorna True se a operação foi bem-sucedida, ou False caso contrário.
    """

    fileRemoved = False
    CopyRemoved = False
    for user in allUsers:
        if not fileRemoved:
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                fileRemoved = proxy.rpc_removeFile(filename)
        
        if not CopyRemoved:
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                CopyRemoved = proxy.rpc_removeCopy(filename)
        
        if fileRemoved and CopyRemoved:
            return True
    
    return False


def userDropped(rmHost, rmPort):
    """! Reorganiza o sistema distribuído quando um usuário desconectou.
    
    @param rmHost Host do usuário desconectado.
    @param rmPort Porta do usuário desconectado.
    """

    global host, port
    allUsers.remove({ "host": rmHost, "port": rmPort })

    # avisando aos outros usuarios q esse usuario dropou
    for user in allUsers:
        if (user["host"] != host) or (user["port"] != port):
            with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
                proxy.rpc_removeUser(rmHost, rmPort)
    
    # Recuperando os arquivos perdidos
    allFiles = []
    for listF in listFiles():
        for f in listF["files"]:
            allFiles.append(f)
    
    copies = listCopies()

    filesToRecover = []

    for copyFiles in copies:
        for copyFile in copyFiles["files"]:
            if not copyFile in allFiles:
                filesToRecover.append({ "file": copyFile, "host": copyFiles["host"], "port": copyFiles["port"] })

    # pegando as copias dos arquivos removidos e 
    for f in filesToRecover:
        with xmlrpc.client.ServerProxy(f"http://{f['host']}:{f['port']}/", allow_none=True) as proxy:
            proxy.rpc_fromCopyToFile(f["file"])

def serverHandler(myHost, myPort, usrHost, usrPort):
    """! Configura e inicia o servidor RPC do usuário.
    
    @param newHost Host que o usuário utilizará.
    """

    global host, port, server, allUsers

    host = myHost
    port = myPort

    # Tenta criar o socket do server
    try:
        server = SimpleXMLRPCServer((host, port), allow_none=True, logRequests=False)
    except OSError:
        print(f"Outro usuario ja existe no endereco {host}:{port}")
        exit(0)
    
    # Tenta fazer contato com o outro usuario passado, se ele foi passado
    if (usrHost != None) and (usrPort != None):
        try:
            with xmlrpc.client.ServerProxy(f"http://{usrHost}:{usrPort}/", allow_none=True) as proxy:
                allUsers = proxy.rpc_connToUser(host, port)
        except:
            print(f"Nao foi encontrado o usuario p/ se conctar no endereco {usrHost}:{usrPort}")
            exit(0)

        # Verifica se usuario foi conectado
        if allUsers == None:
            print(f"Numero maximo de usuarios alcancado na rede do usuario {usrHost}:{usrPort}")
            exit(0)
    
    # Caso n for passado outro usuario, ele se adiciona nem allUsers
    else:
        rpc_newUser(host, port)

    # Verifica se ha outros usuarios online no mesmo host
    # while(port < 8004):
    #     try:
    #         if server == None:
    #             server = SimpleXMLRPCServer((host, port), allow_none=True, logRequests=False)
    #             openPort = port
    #     except OSError:
    #         allUsers.append( {"host": host, "port": port} )
    #     finally:
    #         port += 1
    
    # port = openPort

    # avisando outros usuarios que um novo host conectou
    # if len(allUsers) > 0:
    #     if server != None:
    #         for user in allUsers:
    #             with xmlrpc.client.ServerProxy(f"http://{user['host']}:{user['port']}/", allow_none=True) as proxy:
    #                 proxy.rpc_newUser(host, port)

    #     else:
    #         print("Numero maximo de usuarios ja alcançado!")
    #         exit(0)

    # usuario se adiciona tmb
    # allUsers.append( {"host": host, "port": port} )

    server.register_function(rpc_newUser, "rpc_newUser")
    server.register_function(rpc_getFilesList, "rpc_getFilesList")
    server.register_function(rpc_getFilesTotalSize, "rpc_getFilesTotalSize")
    server.register_function(rpc_receiveNewFile, "rpc_receiveNewFile")
    server.register_function(rpc_removeUser, "rpc_removeUser")
    server.register_function(rpc_getCopiesList, "rpc_getCopiesList")
    server.register_function(rpc_fromCopyToFile, "rpc_fromCopyToFile")
    server.register_function(rpc_renameCopy, "rpc_renameCopy")
    server.register_function(rpc_renameFile, "rpc_renameFile")
    server.register_function(rpc_removeCopy, "rpc_removeCopy")
    server.register_function(rpc_removeFile, "rpc_removeFile")
    server.register_function(rpc_connToUser, "rpc_connToUser")
    
    server.serve_forever()

