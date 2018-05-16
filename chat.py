#coding: utf-8

import thread
import socket
import struct
import gi
import json
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# variável global que vai controlar quando uma thread finalizar
finalizou = 0
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

settings = Gtk.Settings.get_default()
settings.set_property("gtk-theme-name", "Numix")
settings.set_property("gtk-application-prefer-dark-theme", False)  # if you want use dark theme, set second arg to True

class Chat(object):
    def __init__(self):
        builder = Gtk.Builder() #Instancia do Gtk
        builder.add_from_file("chat.glade") #Função para carregar o arquivo
    
        #Widget da janela conectar
        self.window1 = builder.get_object("window1")

        #Widget da janela principal
        self.window2 = builder.get_object("window2")

        #Widget campo da mensagem    
        self.ip_entry = builder.get_object("text_ip_entry")

        self.ip_entry.set_text(MCAST_GRP)

        #Widget campo da mensagem    
        self.nickname_entry = builder.get_object("text_nickname_entry")

        self.nickname_entry.set_text("teste")

        #Widget campo da mensagem    
        self.message_entry = builder.get_object("text_message_entry")

        self.chat = builder.get_object("chat")

        self.chat_scroll = builder.get_object("chat_scroll")

        self.window2.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(.3, .3, .3, 1.0))

        
    	#Exibindo a janela principal do programa
        self.window1.show()

        #trazendo a janela para frente
        self.window1.present()

        #Conectando os sinais(listeners) dos elementos
        builder.connect_signals({"Gtk_main_quit": self.finalizar,
                            #Encerra o programa

                            "on_text_nickname_entry_activate": self.conectar,

                            "on_connect_clicked": self.conectar,
                            #Botao para connectar ao chat

                            "on_text_message_entry_activate": self.enviar,

                            "on_send_clicked": self.enviar,
                            #Botao para enviar mensagem                     
                            })

    def autoscroll(self):
        """The actual scrolling method"""
        adj = self.chat_scroll.get_vadjustment()
        adj.set_value(adj.get_upper())

    def finalizar(self, widget):
        Gtk.main_quit
        raise SystemExit

    def enviar(self, widget):
        data = {}

        data["name"] = self.nickname_entry.get_text()
        data["message"] = self.message_entry.get_text()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(json.dumps(data), (self.ip_entry, MCAST_PORT))
        self.message_entry.set_text("")

    def conectar(self, widget):
        thread.start_new_thread(chat, (self, widget))
        self.window1.hide()

        self.window2.show()
    
    def escrever(self, addr, data):
        if addr[0] == self.getMyIP():
            self.chat.get_buffer().insert_at_cursor("<"+addr[0]+"> "+data["name"]+": "+data["message"] + "\n")
        else:
            self.chat.get_buffer().insert_at_cursor("\t"*25+"<"+addr[0]+"> "+data["name"]+": "+data["message"] + "\n")

        self.autoscroll()

    def getMyIP(self):
        return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


def chat(self, widget):
    # o parâmetro global informa dentro da função, será usada a váriavel chamada finalizou, que existe globalmente no processo.
    # caso não seja passado esse parâmetro a variável, ela será considerada como local da função
    global finalizou
    meunick = self.nickname_entry.get_text()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((self.ip_entry, MCAST_PORT))  # use MCAST_GRP instead of '' to listen only
                                    # to MCAST_GRP, not all groups on MCAST_PORT
    sock.settimeout(1)
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while finalizou != 1:
        try:
            data, addr = sock.recvfrom(10240)
            data = json.loads(data)
            self.escrever(addr, data)
            sock.recvfrom(10240) #ignore second(duplicate)
        except socket.timeout:
            continue
    
    finalizou = 2

if __name__ == "__main__":
    #Cria a instância do programa
    app = Chat()
    
    #Função para manter a janela principal aberta
    Gtk.main() 