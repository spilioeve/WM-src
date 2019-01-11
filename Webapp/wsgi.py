import swagger_server.__main__ as app

app.initialize()
application = app.main()

if __name__ == "__main__":
    application.run()