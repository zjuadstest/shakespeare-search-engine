import json
from term import Term

class Node:
    def __init__(self, is_leaf=True, file_index=-1):
        self.file_index = file_index
        self.is_leaf = is_leaf
        self.n_keys = 0
        self.keys = []
        self.child = []
        self.child_index = []

    def display(self):
        print('is_leaf: ', self.is_leaf)
        print('keys: ', self.keys[0:self.n_keys])
        print('child: ', self.child)
        print("n_keys: ", self.n_keys)
        print("len(keys): ", len(self.keys))
        print("file_index:", self.file_index)
        print("child_index", self.child_index)
        print('\n')

    # convert the node to json style to write on the disk
    def __jsonfy(self):
        d = dict()
        d['file_index'] = self.file_index
        d['is_leaf'] = self.is_leaf
        d['n_keys'] = self.n_keys
        # should be maintained, or read from the children, type(child)
        # d['keys'] = self.keys[0:self.n_keys]
        d['keys'] = list(map(lambda key: key.jsonfy(), self.keys[0:self.n_keys]))
        d['child_index'] = self.child_index
        # print('d: ', d)
        return d

    # get the node data from json document
    def __unjsonfy(self, d):
        self.file_index = d['file_index']
        self.is_leaf = d['is_leaf']
        self.n_keys = d['n_keys']
        # self.keys = d['keys'].unjsonfy()
        # print(d['keys'])
        self.keys = list(map(lambda key: Term().unjsonfy(key), d['keys']))
        self.child_index = d['child_index']
        # bug fixed: should copy by value, not by reference
        self.child = self.child_index[:]  # only replaced by node in buffer when necessary

    def disk_write(self):
        # write node file header: self.file_index, self.n_keys
        with open('data/nodes/node_{0}'.format(self.file_index), 'w') as out:
            json.dump(self.__jsonfy(), out)
            out.close()

    def disk_read(self):
        with open('data/nodes/node_{0}'.format(self.file_index), 'r') as infile:
            self.__unjsonfy(json.load(infile))
            infile.close()


class BTree:
    def __init__(self, degree, node_index=0, root_file_path='data/root'):

        # node_index: the node file index, should be unique, stored in a file
        self.node_index = node_index  # should read from file, otherwise = 0, a new tree

        self.root = Node(True, self.__generate_node_index())  # root: a leaf node
        self.degree = degree  # if degree = 2, 2-3-4 tree

        # DISK-WRITE(self.root)
        self.root.disk_write()
        self.root_path = root_file_path
        self.lru_list = []
        self.lru_size = 30

    def __jsonfy(self):
        d = dict()
        d['node_index'] = self.node_index
        d['degree'] = self.degree
        d['lru_size'] = self.lru_size
        return d

    def __unjsonfy(self, d):
        self.root = Node(True, 0)
        self.root.disk_read()
        self.node_index = d['node_index']
        self.degree = d['degree']
        self.lru_size = d['lru_size']

    def disk_write(self):
        for node in self.lru_list:
            node.disk_write()
        self.root.disk_write()
        with open(self.root_path, 'w') as out:
            json.dump(self.__jsonfy(), out)
            out.close()

    def disk_read(self):
        with open(self.root_path, 'r') as infile:
            # print(self.root_path)
            # print(infile.read())
            self.__unjsonfy(json.load(infile))
            infile.close()

    def __insert_lru(self, node):
        self.lru_list.append(node)
        if len(self.lru_list) > self.lru_size:
            self.lru_list[0].disk_write()
            self.lru_list.pop(0)

    def __is_in_lru(self, node):
        if node == self.root:
            return True
        return node in self.lru_list

    def __lru_high_priority(self, node):
        self.lru_list.append(self.lru_list.pop(self.lru_list.index(node)))

    def __generate_node_index(self):
        self.node_index += 1
        # print("generate index: {0}".format(self.node_index - 1))
        return self.node_index - 1

    def __search(self, node, search_key):
        # find the bigger or equal key on the tree
        i = 0
        while i < node.n_keys and search_key > node.keys[i]:
            i += 1

        # when search_key >= self.keys[i]
        # if this is a leaf node
        if i < node.n_keys and search_key == node.keys[i]:
            return node, i
        elif node.is_leaf:
            return None
        else:
            # DISK-READ(node.child[i])
            # if the child is not in buffer, read it firstly
            if not self.__is_in_lru(node.child[i]):
                node.child[i] = Node(file_index=node.child_index[i])
                node.child[i].disk_read()
                self.__insert_lru(node.child[i])
            else:
                # make high priority
                self.__lru_high_priority(node.child[i])

            return self.__search(node.child[i], search_key)

    def __split_child(self, node, ith_child):
        left_child = node.child[ith_child]
        right_child = Node(left_child.is_leaf, self.__generate_node_index())  # right sub of the tree, newly created
        right_child.n_keys = self.degree - 1
        self.__insert_lru(right_child)
        for j in range(0, self.degree - 1):
            right_child.keys.append(left_child.keys[j + self.degree])
        if not left_child.is_leaf:
            for j in range(0, self.degree):
                right_child.child.append(left_child.child[j + self.degree])
                right_child.child_index.append(left_child.child_index[j + self.degree])
        left_child.n_keys = self.degree - 1  # dummy deletion

        # shift relative right ones in node one place right

        if ith_child == node.n_keys:  # if it is the end child
            # if there's no dummy space
            if len(node.keys) == node.n_keys:
                node.child.append(right_child)
                node.child_index.append(right_child.file_index)
                node.keys.append(left_child.keys[self.degree - 1])  # use the first dummy node, i.e. the new root
            else:
                node.child[node.n_keys + 1] = right_child
                node.child_index[node.n_keys + 1] = right_child.file_index
                node.keys[node.n_keys] = left_child.keys[self.degree - 1]
            node.n_keys += 1
            return

        # if no dummy space
        if len(node.keys) == node.n_keys:
            node.child.append(node.child[node.n_keys])
            node.child_index.append(node.child_index[node.n_keys])
        else:  # dummy space remaining
            node.child[node.n_keys + 1] = node.child[node.n_keys]
            node.child_index[node.n_keys + 1] = node.child_index[node.n_keys]

        for j in range(node.n_keys - 1, ith_child, -1):
            node.child[j + 1] = node.child[j]
            node.child_index[j + 1] = node.child_index[j]
        node.child[ith_child + 1] = right_child
        node.child_index[ith_child + 1] = right_child.file_index

        # shift keys one place right
        # if no dummy space
        if len(node.keys) == node.n_keys:
            node.keys.append(node.child[node.n_keys - 1])
        else:
            node.keys[node.n_keys] = node.child[node.n_keys - 1]
        for j in range(node.n_keys - 1, ith_child - 1, -1):
            node.keys[j + 1] = node.keys[j]
        node.keys[ith_child] = left_child.keys[self.degree - 1]
        node.n_keys += 1
        # DISK-WRITE(node)
        # node.disk_write()
        # DISK-WRITE(left_child)
        # left_child.disk_write()
        # DISK-WRITE(right_child)
        # right_child.disk_write()

    def __insert_nonfull(self, node, key):
        # base case, if it is empty root
        if node.n_keys == 0:
            node.keys.append(key)
            node.n_keys += 1
            return node, (node.n_keys - 1)

        i = node.n_keys - 1  # the last node

        # base case, insert directly
        if node.is_leaf:
            # if key is the biggest, insert at the right side directly
            if key > node.keys[node.n_keys - 1]:
                # if no dummy space
                if len(node.keys) == node.n_keys:
                    node.keys.append(key)
                else:
                    node.keys[node.n_keys] = key
                node.n_keys += 1
                return node, (node.n_keys - 1)
            else:
                if len(node.keys) == node.n_keys:  # no dummy space
                    node.keys.append(node.keys[node.n_keys - 1])  # 0 .. n_keys after appending
                else:
                    node.keys[node.n_keys] = node.keys[node.n_keys - 1]

                # if only 2 nodes, insert after the first node right
                if i == 0:
                    node.keys[0] = key
                    node.n_keys += 1
                    return node, 0

                while i >= 1 and key < node.keys[i]:
                    node.keys[i] = node.keys[i - 1]
                    i -= 1

                node.keys[i + 1] = key  # replace the 'i-1' above

                node.n_keys += 1
                return node, (i + 1)
            # DISK-WRITE(node)
            # node.disk_write()
        else:
            # key >= ith key, go to the (i+1)th child
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            # DISK-READ(node.child[i])
            # i
            if not self.__is_in_lru(node.child[i]):
                # if already created
                # TODO: fix node_-1 (done)
                # if pathlib.Path('data/nodes/node_{0}'.format).is_file():
                # if not created yet
                node.child[i] = Node(file_index=node.child_index[i])
                node.child[i].disk_read()
                self.__insert_lru(node.child[i])
                # TODO: (No issue at all!)
                #  1. Fix LRU List Empty (Done)
                #  2. Index Node not splitting: Check B Tree Node (Done)
            else:
                # make high priority
                self.__lru_high_priority(node.child[i])

            if node.child[i].n_keys == (2 * self.degree - 1):
                self.__split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            # print("ith-child: ", i)
            return self.__insert_nonfull(node.child[i], key)

    def search(self, search_key):
        return self.__search(self.root, search_key)

    def insert(self, key):
        root = self.root
        if self.root.n_keys == 2 * self.degree - 1:
            self.root = Node(False, 0)
            self.__insert_lru(root)
            root.file_index = self.__generate_node_index()
            self.root.child.append(root)  # original root as left child
            self.root.child_index.append(root.file_index)
            self.__split_child(self.root, 0)
            return self.__insert_nonfull(self.root, key)
        return self.__insert_nonfull(root, key)


# TODO:
#  (DONE) 1. solve dummy deletion and later append conflict
#  - compare list length with the length in the record
#  2. Tests on higher degree B Tree


# ## block test
def test_insertion():
    btree = BTree(2)
    btree.insert(1)
    btree.insert(6)
    # insert between
    btree.insert(4)

    # should split child
    btree.insert(7)

    # another split right side
    btree.insert(9)
    btree.insert(5)
    #

    btree.insert(8)
    btree.insert(10)
    btree.insert(11)
    btree.insert(12)
    # print("inserting 2:")
    # btree.insert(2)

    btree.root.display()
    for c in btree.root.child:
        c.display()


def test_disk_write():
    print('test: disk_write')
    btree = BTree(2)
    btree.insert(1)
    btree.insert(6)
    btree.insert(4)
    btree.insert(10)
    btree.insert(11)
    btree.insert(12)
    btree.root.display()
    btree.root.disk_write()
    for child in btree.root.child:
        child.display()
        child.disk_write()


def test_disk_read():
    print('test: disk_read')
    root = Node(True, 0)
    root.disk_read()
    root.display()

    # test: load as list
    print(root.keys[1])

# test_disk_write()
# test_disk_read()






