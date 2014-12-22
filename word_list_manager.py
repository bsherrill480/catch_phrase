from os import listdir
from weakref import WeakValueDictionary
import cPickle as pickle
PATH_TO_WORDS = "./words/"
PATH_TO_PREMIUM_WORDS = "./premium_words/"
# class WordManagerWeak(dict):
#     """
#     weakref did not work, so I'll just manually keep track of references in my code.
#     for the small amount of code I have this will not be an issue, however this should
#     not be extended to a larger project.
#     """
#     def __init__(self, *args, **kwargs):
#         dict.__init__(self, *args, **kwargs)
#         self.lists_names = listdir(PATH_TO_WORDS)
#         self.references_to_list = {list_name : 0 for list_name in self.lists_names}
#         print "choices: ", listdir(PATH_TO_WORDS)
#
#     def __getitem__(self, name):
#         if name in self:
#             value = dict.__getitem__(self, name)
#             return value
#         else:
#             print "building word list"
#             try:
#                 with open(PATH_TO_WORDS + name, "rb") as file:
#                     words_list = pickle.load(file)
#                     self[name] = words_list
#                     print "keys: ", self.keys(), "values", self.values()
#                     return words_list
#             except IOError, err:
#                 if err[0]: #i.e. No such file or directory
#                     raise KeyError(name)
#                 else:
#                     raise err
#
#     def done_with_list(self, list_name):
#         num_ref = self[list_name]
#         if num_ref <= 0:
#             del self[list_name]

class WordManager(dict):
    """
    scew it. Load everything
    """
    def __init__(self, word_list_location):
        if word_list_location == "free":
            path = PATH_TO_WORDS
        elif word_list_location == "premium":
            path = PATH_TO_PREMIUM_WORDS
        else:
            path = word_list_location
        dict.__init__(self)
        self.lists_names = listdir(path)
        for name in self.lists_names:
            with open(path + name, "rb") as file:
                words_list = pickle.load(file)
                self[name] = words_list

# class WordManagerWeak2(WeakValueDictionary):
#     """
#     DOES NOT WORK. RELEASES DATA AFTER LOADING IT
#     names of the items in list are they also the keys to the lists
#     e.g. animals is the name of the list, and the key to get the list
#     of animal words.
#     """
#     def __init__(self, *args, **kwargs):
#         WeakValueDictionary.__init__(self, *args, **kwargs)
#         print "my values", self.values()
#         self.lists_names = listdir(PATH_TO_WORDS)
#         print "choices: ", listdir(PATH_TO_WORDS)
#
#     def __getitem__(self, name):
#         if name in self:
#             value = WeakValueDictionary.__getitem__(self, name)
#             assert value is not None # just to be sure
#             return value
#         else:
#             print "building word list"
#             try:
#                 with open(PATH_TO_WORDS + name, "rb") as file:
#                     words_list = WeakList(pickle.load(file))
#                     self[name] = words_list
#                     print "keys: ", self.keys(), "values", self.values()
#                     return words_list
#             except IOError, err:
#                 if err[0]: #i.e. No such file or directory
#                     raise KeyError(name)
#                 else:
#                     raise err
#
#     def keys(self):
#         #print "keys called"
#         return WeakValueDictionary.keys(self)

class WeakList(list):
    pass

if __name__ == "__main__":
    def add_list(name, word_list):
        """
        adda a list of words on file.
        """
        lists_names = listdir(PATH_TO_WORDS)
        if name in lists_names:
            raise KeyError("name is already taken")
        elif not isinstance(word_list, list):
            raise TypeError("Must be a list")
        else:
            with open(PATH_TO_WORDS + name, "w+") as file:
                pickle.dump(word_list, file, -1)

    a = WordManager()
    for name in a.lists_names:
        add_list(name + "2", list(a[name]))

# data1 = {'a': [1, 2.0, 3, 4+6j],
#          'b': ('string', u'Unicode string'),
#          'c': None}
#
# selfref_list = [1, 2, 3]
# selfref_list.append(selfref_list)
#
# output = open('data', 'wb')
#
# # Pickle dictionary using protocol 0.
# pickle.dump(data1, output)
#
# # Pickle the list using the highest protocol available.
# pickle.dump(selfref_list, output, -1)
#
# output.close()

# import pprint
# import cPickle as pickle
#
# pkl_file = open('data', 'rb')
#
# data1 = pickle.load(pkl_file)
# pprint.pprint(data1)
#
# data2 = pickle.load(pkl_file)
# pprint.pprint(data2)
#
# pkl_file.close()
