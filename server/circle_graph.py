class Node:
    """
    its a node
    """
    def __init__(self, data=None, name=None):
        self.next = next
        self.data = data
        self.name = name

class Organizer:
    """
    class to interact with data.
    Uses nodes
    """
    def __init__(self):
        self.nodes = dict()

    def make_and_give_node(self, data, name):
        """
        makes a node with passed name and data
        """
        node = Node(data, name)
        self.nodes[name] = node
        return node

    # def set_next(self, name, next_item_name):
    #     """
    #
    #     """
    #     self.nodes[name].next = self.nodes[next_item_name]

    def set_next(self, name1, name2):
        """
        makes name1's node's next name2's node.
        """
        node1 = self.nodes[name1]
        node2 = self.nodes[name2]
        node1.next = node2

    def delete_node(self, name):
        """
        deletes a node from circle
        """
        del self.nodes[name]

    def is_perfect_circle(self):
        """
        returns true if is perfect circle, else false.
        """
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

    def client_id_lists(self):
        """
        returns list of (list of client_id's showing cycles). See visual_nodes()
        understanding list format.
        """
        # master_list = []
        # list_of_cycles = self.visual_nodes()
        # for cycle in list_of_cycles:
        #     one_cycle = []
        #     for node in cycle:
        #         one_cycle.append(node.client_id)
        #     master_list.append(one_cycle)
        #
        # return master_list
        return [[node.data.client_id for node in cycle]for cycle in self.visual_nodes()]

    def visual_strings(self):
        """
        returns list of strings which contain nicknames showing cycles.
        e.g. "a,b,c,d,a"
        See visual_nodes() understanding list format.
        """
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
        returns list of (lists where the leading node points is pointing at
        the next node). e.g.
        a ->b
        b ->c
        c ->d
        d ->a
        the list would look like [[a,b,c,d,a]]
        but if
        a ->b
        b ->c
        c ->d
        d ->c
        you would get something like [[a,b,c,d,c]] or [[d,c,d], [a,b,c,d,c]].

        algorithm used:
        make master_list. call step1 (below) with set of all nodes.
        step1) pick random node in set of nodes, add it to list called node_seq.
        keep going until we either none or the start node. add node_seq to master list.

        step2)If there are any leftover nodes, do step1 again remaining nodes.
        """
        master_list = []
        self._visual_helper(master_list, set(self.nodes.values()))
        return master_list

    def _visual_helper(self, master_list, unused_nodes):
        """
        helper method for visual_nodes()
        """
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
            self._visual_helper(master_list, unused_nodes)

if __name__ == '__main__':
    #for debugging
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
    node4.next = node3


    for node in l:
        organizer.nodes[node.name] = node
    print organizer.is_perfect_circle()
    vis = organizer.visual_nodes()
    for loop in vis:
        print [x.name for x in loop]