from os import listdir
import cPickle as pickle
PATH_TO_WORDS = "./words/"
PATH_TO_PREMIUM_WORDS = "./premium_words/"

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
        try:
            self.lists_names = listdir(path)
            for name in self.lists_names:
                with open(path + name, "rb") as file:
                    words_list = pickle.load(file)
                    words_list = words_list.sort()
                    self[name] = words_list
        except:
            self["Offline"] = []
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
            with open(PATH_TO_WORDS + name , "w+") as file:
                pickle.dump(word_list, file, -1)
    dir_with_files = "./word_lists/"
    wordlists_files_to_add = listdir(dir_with_files)
    wordlists_names_to_add = [word.split(".")[0] for word in wordlists_files_to_add]
    wordlists_files_to_add = [ dir_with_files + file for file in wordlists_files_to_add]
    for file in wordlists_files_to_add:
        with open(file, "r") as f:
            l = f.read().decode("utf-8-sig").encode("utf-8")
            l = l.splitlines()
            l = [i.strip(" ") for i in l]
            l = filter(lambda a: a != "", l)
        name = wordlists_names_to_add[wordlists_files_to_add.index(file)]
        print l
        #add_list(name, l)
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
