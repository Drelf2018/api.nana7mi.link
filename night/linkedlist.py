class LinkedList:

    class Node:
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

    def getHead(self):
        return self.__head

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
    
    def print(self):
        current_node = self.__head
        while current_node:
            print(current_node.getValue(), end=' ')
            current_node = current_node.getNext()
        print()


if __name__ == '__main__':
    ll = LinkedList(5)
    for _ in range(10):
        ll.append(_)
        ll.print()