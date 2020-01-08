from Server import Server

if __name__ == '__main__':
    s = Server(1, 3117)
    s.listen()
    s.close()
