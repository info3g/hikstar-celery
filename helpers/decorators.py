from threading import Thread


def run_async(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.start()

    return decorator
