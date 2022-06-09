from logging import StreamHandler, Formatter


class LinkedList:
    '定长链表'
    class Node:
        '链表内节点'
        def __init__ (self, value = None, next = None):
            self.__value = value
            self.__next = next

        def getValue(self):
            return self.__value

        def getNext(self):
            return self.__next

        def setNext(self, new_next):
            self.__next = new_next

    def __init__(self, maxLength: int = 100, data=None):
        self.__head = None
        self.__tail = None
        self.__length = 0
        self.__maxLength = maxLength
        if data:
            self.append(data)

    # 获取head节点
    def getHead(self):
        return self.__head

    # 获取一个指向head节点的假节点
    def getTrueHead(self):
        return self.Node(next=self.__head)

    # 检测是否为空
    def isEmpty(self):
        return self.__length == 0

    # append在链表尾部添加元素
    def append(self, value):
        if self.isEmpty():
            self.__head = self.Node(value)
            self.__tail = self.__head
        else:
            last_node, self.__tail = self.__tail, self.Node(value)
            last_node.setNext(self.__tail)
        self.__length += 1
        for _ in range(self.__length - self.__maxLength):
            self.pop()

    # pop删除链表中的第一个元素
    def pop(self):
        if self.__length > 0:
            self.__length -= 1
            temp = self.__head
            self.__head = self.__head.getNext()
            return temp
    
    # 遍历输出元素
    def print(self):
        current_node = self.__head
        while current_node:
            print(current_node.getValue(), end='->')
            current_node = current_node.getNext()
        print()


class WebHandler(StreamHandler):
    '自定义 Logger Handler'
    def __init__(self, stream=None, loglist=LinkedList(20)):
        super().__init__(stream)
        self.loglist = loglist

    def emit(self, record):
        try:
            msg = self.format(record)
            self.loglist.append(msg)  # 相比原方法多了这一句 作用是把打印到控制台的消息保存进链表
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def get_default_handler(size: int = 20):
    '获取一个可遍历链表和 Logger Handler'
    loglist = LinkedList(size)
    handler = WebHandler(loglist=loglist)
    handler.setFormatter(Formatter(f'`%(asctime)s` `%(levelname)s`: %(message)s', '%Y-%m-%d %H:%M:%S'))
    return loglist, handler


if __name__ == '__main__':
    from logging import Logger, DEBUG
    logger = Logger('MAIN', DEBUG)
    loglist, handler = get_default_handler()
    logger.addHandler(handler)
    for _ in range(5):
        logger.info(('Admin', _))
        loglist.print()