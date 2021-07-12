import time

class Timer:
    def __enter__(self):
        self.a = time.perf_counter()

    def __exit__(self, *error):
        self.b = time.perf_counter()
        print(f'{self.b-self.a:.8f} seconds')

    async def __aenter__(self):
        self.a = time.perf_counter()

    async def __aexit__(self, *error):
        self.b = time.perf_counter()
        print(f'{self.b-self.a:.8f} seconds')