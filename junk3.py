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

import pprint
import cPickle as pickle

with open('datsdfsa', 'rb') as pkl_file:
    data1 = pickle.load(pkl_file)
    pprint.pprint(data1)
    data2 = pickle.load(pkl_file)
    pprint.pprint(data2)

