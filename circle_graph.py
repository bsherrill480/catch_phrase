class Node:
    def __init__(self, data=None, name=None):
        self.next = next
        self.data = data
        self.name = name

class Organizer:
    def __init__(self):
        self.nodes = dict()

    def make_and_give_node(self, data, name):
        node = Node(data, name)
        self.nodes[name] = node
        return node

    def set_next(self, name, next_item_name):
        self.nodes[name].next = self.nodes[next_item_name]

    def point(self, name1, name2):
        node1 = self.nodes[name1]
        node2 = self.nodes[name2]
        node1.next = node2

    def delete_node(self, name):
        del self.nodes[name]

    def is_perfect_circle(self):
        in_circle_set = set()
        start_node = self.nodes.itervalues().next()
        in_circle_set.add(start_node)
        examine_node = start_node.next
        while examine_node is not start_node:
            if (examine_node in in_circle_set) or (examine_node is None):
                return False
            in_circle_set.add(examine_node)
            examine_node = examine_node.next
        return len(self.nodes) == len(in_circle_set)

    def visual_strings(self):
        master_list = []
        list_of_cycles = self.visual_nodes()
        for cycle in list_of_cycles:
            one_cycle = ""
            for node in cycle:
                one_cycle = one_cycle + node.data.nickname + " "
            master_list.append(one_cycle)
        return master_list

    def visual_nodes(self):
        """
        returns list of (lists which have visible each item as a node)
        """
        master_list = []
        self.visual_helper(master_list, set(self.nodes.values()))
        return master_list
    def visual_helper(self, master_list, unused_nodes):
        if unused_nodes: #if not empty
            node_seq = []
            used_nodes = set()
            start_node = unused_nodes.__iter__().next()
            used_nodes.add(start_node)
            node_seq.append(start_node)
            examine_node = start_node.next
            while True:
                if examine_node in used_nodes:
                    node_seq.append(examine_node)
                    break
                if examine_node is None:
                    break
                used_nodes.add(examine_node)
                node_seq.append(examine_node)
                examine_node = examine_node.next
            master_list.append(node_seq)
            unused_nodes = unused_nodes.difference(used_nodes)
            self.visual_helper(master_list, unused_nodes)

if __name__ == '__main__':
    node1 = Node(None, "1")
    node2 = Node(None, "2")
    node3 = Node(None, "3")
    node4 = Node(None, "4")
    organizer = Organizer()

    l = [node1, node2, node3, node4]
    for i in range(len(l)):
        if i == len(l) - 1:
            j = 0
        else:
            j = i + 1
        node = l[i]
        node.next = l[j]
    #printing to see
    for node in l:
        print node.next.name
    node3.next = node1
    node1.next = node3
    node3.next = node2
    node2.next= node4

    for node in l:
        organizer.nodes[node.name] = node
    print organizer.is_perfect_circle()
    vis = organizer.visual()
    for loop in vis:
        print [x for x in loop]