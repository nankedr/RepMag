class SensInfo:
    def __init__(self, taskid, verb, name, value):
        self.taskid = taskid
        self.verb = verb
        self.name = name
        self.value = value

    def __str__(self):
        return ','.join(str(i) for i in [self.taskid, self.verb, self.name, self.value])

    @classmethod
    def from_string(cls, data):
        return SensInfo(*data.split(','))

    @staticmethod
    def test():
        si = SensInfo(0, 'set', 'sensing', 50)
        print(str(si))
        print(SensInfo.from_string(str(si)))


if __name__ == '__main__':
    SensInfo.test()
